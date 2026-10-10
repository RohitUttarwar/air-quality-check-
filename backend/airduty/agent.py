"""AWS Strands Agents SDK integration with Amazon Bedrock.

Uses Bedrock via Strands tools for contextual bilingual drafting with 100% reliable
fallback to the deterministic rules engine when offline or if Bedrock is unreachable.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from airduty.aqi import calculate_cpcb_aqi
from airduty.data import AirDataReport, get_air_data, load_demo_fixture
from airduty.rules import (
    DecisionOutput,
    SchoolPolicy,
    evaluate_school_safety,
)

logger = logging.getLogger(__name__)

# Fallback model ID if environment variable BEDROCK_MODEL_ID is unset
DEFAULT_BEDROCK_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"

try:
    from strands import Agent, tool
    from strands.models import BedrockModel
    STRANDS_AVAILABLE = True
except ImportError:
    STRANDS_AVAILABLE = False
    logger.warning("strands package not found; agent will run in pure deterministic mode.")


# Tool definitions for Strands Agents SDK
if STRANDS_AVAILABLE:
    @tool
    def get_air_quality(lat: float, lon: float, demo: bool = False) -> str:
        """Fetch current PM2.5 and PM10 air quality telemetry for a location."""
        report = load_demo_fixture() if demo else get_air_data(lat=lat, lon=lon)
        return json.dumps({
            "timestamp": report.current.timestamp,
            "pm25": report.current.pm25,
            "pm10": report.current.pm10,
            "source": report.current.source,
            "is_demo": report.is_demo,
        })

    @tool
    def get_forecast(lat: float, lon: float, demo: bool = False) -> str:
        """Fetch hourly air quality forecast for the next 24 hours."""
        report = load_demo_fixture() if demo else get_air_data(lat=lat, lon=lon)
        pts = [
            {"time": p.time, "pm25": p.pm25, "pm10": p.pm10, "cpcb_aqi": p.cpcb_aqi}
            for p in report.forecast[:12]
        ]
        return json.dumps(pts)

    @tool
    def compute_cpcb_aqi(pm25: float, pm10: float) -> str:
        """Compute the official Indian CPCB sub-index and AQI category."""
        res = calculate_cpcb_aqi(pm25=pm25, pm10=pm10)
        return json.dumps(res.to_dict())

    @tool
    def get_school_policy(school_id: str = "default") -> str:
        """Retrieve school safety policy thresholds."""
        policy = SchoolPolicy()
        return json.dumps(policy.to_dict())

    @tool
    def draft_alert(headline: str, status_level: str, aqi: int, category: str, sensitive_count: int) -> str:
        """Draft standard emergency alerts for school administration."""
        return json.dumps({
            "status": "ready",
            "headline": headline,
            "status_level": status_level,
            "aqi": aqi,
            "category": category,
            "sensitive_count": sensitive_count,
        })
else:
    # Dummy tool placeholders if strands is missing
    get_air_quality = None
    get_forecast = None
    compute_cpcb_aqi = None
    get_school_policy = None
    draft_alert = None


class AgentDecisionResponse(BaseModel):
    headline: str
    status_level: str
    pe_action: str
    assembly_action: str
    recess_action: str
    mask_advisory: str
    ventilation_advice: str
    reasons: List[str]
    principal_message_en: str
    parent_message_en: str
    parent_message_hi: str
    agent_mode: str = Field(description="bedrock_strands or deterministic_fallback")
    model_id_used: str


class AirDutyAgent:
    """Agentic Air Duty Officer powered by Strands Agents SDK and Amazon Bedrock."""

    def __init__(self, model_id: Optional[str] = None, region: Optional[str] = None):
        self.model_id = (
            model_id
            or os.environ.get("BEDROCK_MODEL_ID")
            or DEFAULT_BEDROCK_MODEL
        )
        self.region = (
            region
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "ap-south-1"
        )
        self._init_strands_agent()

    def _init_strands_agent(self) -> None:
        self.strands_agent = None
        if not STRANDS_AVAILABLE:
            return

        # Check if AWS credentials or Bedrock is configured
        has_aws_creds = bool(
            os.environ.get("AWS_ACCESS_KEY_ID")
            or os.environ.get("AWS_SESSION_TOKEN")
            or os.path.exists(os.path.expanduser("~/.aws/credentials"))
        )

        if not has_aws_creds:
            logger.info("No AWS credentials found; agent initialized with deterministic fallback.")
            return

        try:
            model = BedrockModel(
                model_id=self.model_id,
                region_name=self.region,
            )
            self.strands_agent = Agent(
                model=model,
                tools=[
                    get_air_quality,
                    get_forecast,
                    compute_cpcb_aqi,
                    get_school_policy,
                    draft_alert,
                ],
                system_prompt=(
                    "You are the Air Duty Officer for an Indian school. "
                    "Analyze air pollution telemetry and forecast data. "
                    "You must NEVER relax safety thresholds determined by policy. "
                    "Draft clear, empathetic, non-technical instructions for the principal and parents "
                    "in both English and Hindi."
                ),
            )
        except Exception as exc:
            logger.warning("Could not initialize BedrockModel (%s); deterministic fallback will be used.", exc)
            self.strands_agent = None

    def run_evaluation(
        self,
        report: AirDataReport,
        policy: Optional[SchoolPolicy] = None,
        sensitive_students_count: int = 45,
    ) -> AgentDecisionResponse:
        """Run air safety evaluation.

        SAFETY INVARIANT:
        The deterministic rules engine determines safety bounds (PE, assembly, recess, masks).
        Bedrock/Strands refines explanations and phrasing.
        If Bedrock fails or credentials are absent, the deterministic rules engine provides
        immediate, guaranteed fallback.
        """
        if policy is None:
            policy = SchoolPolicy()

        # Step 1: Compute deterministic baseline
        baseline: DecisionOutput = evaluate_school_safety(
            report=report,
            policy=policy,
            sensitive_students_count=sensitive_students_count,
        )

        # Step 2: Attempt Bedrock LLM drafting if available
        if self.strands_agent is not None:
            try:
                user_prompt = (
                    f"Current CPCB AQI is {baseline.current_aqi} ({baseline.current_category}). "
                    f"PM2.5 is {report.current.pm25} µg/m³. "
                    f"Peak forecast AQI is {baseline.peak_forecast_aqi}. "
                    f"Policy mandates: PE={baseline.pe_action}, Assembly={baseline.assembly_action}, "
                    f"Masks={baseline.mask_advisory}, Ventilation={baseline.ventilation_advice}. "
                    f"Sensitive students: {sensitive_students_count}. "
                    f"Please provide tailored, polite messages for the principal and parents in English and Hindi. "
                    f"Output strictly in JSON format matching the schema."
                )
                response = self.strands_agent(user_prompt)
                raw_text = str(response)

                # Attempt to extract JSON from Bedrock response
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1:
                    parsed = json.loads(raw_text[start : end + 1])
                    return AgentDecisionResponse(
                        headline=baseline.headline,
                        status_level=baseline.status_level,
                        pe_action=baseline.pe_action,  # Preserved from deterministic engine
                        assembly_action=baseline.assembly_action,  # Preserved
                        recess_action=baseline.recess_action,  # Preserved
                        mask_advisory=baseline.mask_advisory,  # Preserved
                        ventilation_advice=baseline.ventilation_advice,  # Preserved
                        reasons=baseline.reasons,
                        principal_message_en=parsed.get("principal_message_en", baseline.principal_message_en),
                        parent_message_en=parsed.get("parent_message_en", baseline.parent_message_en),
                        parent_message_hi=parsed.get("parent_message_hi", baseline.parent_message_hi),
                        agent_mode="bedrock_strands",
                        model_id_used=self.model_id,
                    )
            except Exception as exc:
                logger.warning("Bedrock agent invocation failed (%s); using deterministic fallback.", exc)

        # Step 3: Pure deterministic fallback (zero external dependencies)
        return AgentDecisionResponse(
            headline=baseline.headline,
            status_level=baseline.status_level,
            pe_action=baseline.pe_action,
            assembly_action=baseline.assembly_action,
            recess_action=baseline.recess_action,
            mask_advisory=baseline.mask_advisory,
            ventilation_advice=baseline.ventilation_advice,
            reasons=baseline.reasons,
            principal_message_en=baseline.principal_message_en,
            parent_message_en=baseline.parent_message_en,
            parent_message_hi=baseline.parent_message_hi,
            agent_mode="deterministic_fallback",
            model_id_used=self.model_id,
        )
