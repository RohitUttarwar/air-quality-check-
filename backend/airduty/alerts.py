"""Amazon SNS alert dispatcher for Air Duty Officer.

Publishes morning operational directives via SNS (Email/SMS) with local fallback.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def publish_sns_alert(
    subject: str,
    message: str,
    topic_arn: Optional[str] = None,
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Publish an operational directive message to an Amazon SNS topic.

    If SNS topic is not configured or AWS credentials are unavailable,
    logs the alert and returns a simulated status so the app continues seamlessly.
    """
    arn = topic_arn or os.environ.get("SNS_TOPIC_ARN", "").strip()
    target_region = region or os.environ.get("AWS_REGION", "ap-south-1")

    # If no valid topic ARN is provided, simulate delivery locally
    if not arn or arn.startswith("arn:aws:sns:ap-south-1:123456789012"):
        logger.info("[ALERT DISPATCH - LOCAL SIMULATION]\nSubject: %s\nBody:\n%s", subject, message)
        return {
            "status": "SIMULATED_LOCAL",
            "message_id": f"simulated-{os.urandom(4).hex()}",
            "topic_arn": arn or "none",
            "note": "SNS Topic ARN not configured; alert recorded locally.",
        }

    try:
        sns_client = boto3.client("sns", region_name=target_region)
        # Ensure subject is under 100 characters per SNS limit
        safe_subject = subject[:98] if len(subject) > 98 else subject
        response = sns_client.publish(
            TopicArn=arn,
            Subject=safe_subject,
            Message=message,
        )
        msg_id = response.get("MessageId", "unknown")
        logger.info("Published SNS alert successfully: MessageId=%s", msg_id)
        return {
            "status": "DELIVERED_SNS",
            "message_id": msg_id,
            "topic_arn": arn,
        }
    except (ClientError, Exception) as exc:
        logger.error("Failed to publish SNS alert (%s); falling back to local logging", exc)
        return {
            "status": "FAILED_FALLBACK_LOCAL",
            "error": str(exc),
            "topic_arn": arn,
        }


def format_bulletin_for_sns(decision_output: Dict[str, Any], school_name: str) -> str:
    """Format full multi-channel notification for SNS email broadcast."""
    headline = decision_output.get("headline", "Air Quality Notice")
    current_aqi = decision_output.get("current_aqi", "N/A")
    category = decision_output.get("current_category", "N/A")
    pe = decision_output.get("pe_action", "").replace("_", " ").title()
    assembly = decision_output.get("assembly_action", "").replace("_", " ").title()
    recess = decision_output.get("recess_action", "").replace("_", " ").title()
    masks = decision_output.get("mask_advisory", "").replace("_", " ").title()
    ventilation = decision_output.get("ventilation_advice", "").replace("_", " ").title()

    reasons = "\n".join(f"- {r}" for r in decision_output.get("reasons", []))

    parent_en = decision_output.get("parent_message_en", "")
    parent_hi = decision_output.get("parent_message_hi", "")

    return f"""====================================================
🏫 AIR DUTY OFFICER - MORNING OPERATIONAL DISPATCH
====================================================
School: {school_name}
Direct Action: {headline}
CPCB AQI: {current_aqi} ({category})

MANDATORY PROTOCOLS FOR TODAY:
- Outdoor PE: {pe}
- Assembly: {assembly}
- Recess: {recess}
- Mask Advisory: {masks}
- Classroom Ventilation: {ventilation}

KEY REASONS:
{reasons}

----------------------------------------------------
COMMUNICATION FOR PARENTS (ENGLISH):
"{parent_en}"

COMMUNICATION FOR PARENTS (HINDI / हिन्दी):
"{parent_hi}"
----------------------------------------------------
Generated automatically by Air Duty Officer (AWS Serverless + Strands Agents)
"""
