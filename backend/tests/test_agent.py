"""Unit tests for Strands agent and Bedrock integration."""

import json
import os
from unittest.mock import MagicMock, patch
import pytest

from airduty.agent import (
    AirDutyAgent,
    compute_cpcb_aqi,
    draft_alert,
    get_air_quality,
    get_forecast,
    get_school_policy,
)
from airduty.data import load_demo_fixture


def test_agent_tools_execution():
    # Test tool 1: get_air_quality
    aq_json = get_air_quality(lat=28.6139, lon=77.2090, demo=True)
    aq_data = json.loads(aq_json)
    assert "pm25" in aq_data
    assert aq_data["is_demo"] is True

    # Test tool 2: get_forecast
    fc_json = get_forecast(lat=28.6139, lon=77.2090, demo=True)
    fc_data = json.loads(fc_json)
    assert len(fc_data) > 0
    assert "cpcb_aqi" in fc_data[0]

    # Test tool 3: compute_cpcb_aqi
    cpcb_json = compute_cpcb_aqi(pm25=315.0, pm10=460.0)
    cpcb_data = json.loads(cpcb_json)
    assert cpcb_data["category"] == "Severe"

    # Test tool 4: get_school_policy
    pol_json = get_school_policy("test-school")
    pol_data = json.loads(pol_json)
    assert pol_data["pe_indoor_threshold"] == 201

    # Test tool 5: draft_alert
    al_json = draft_alert(headline="Test Alert", status_level="HAZARDOUS", aqi=450, category="Severe", sensitive_count=30)
    al_data = json.loads(al_json)
    assert al_data["status"] == "ready"


def test_agent_model_id_from_env(monkeypatch):
    test_model = "amazon.nova-micro-v1:0"
    monkeypatch.setenv("BEDROCK_MODEL_ID", test_model)
    agent = AirDutyAgent()
    assert agent.model_id == test_model


def test_agent_deterministic_fallback():
    # When no AWS credentials are configured, agent must fall back cleanly
    report = load_demo_fixture()
    agent = AirDutyAgent()
    # Force agent.strands_agent to None to test pure fallback path
    agent.strands_agent = None

    response = agent.run_evaluation(report=report, sensitive_students_count=45)
    assert response.agent_mode == "deterministic_fallback"
    assert response.status_level == "HAZARDOUS"
    assert response.pe_action == "indoor_only"
    assert response.mask_advisory == "mandatory_all"
    assert len(response.reasons) == 3
    assert len(response.parent_message_en) > 0
    assert "अभिभावक" in response.parent_message_hi


def test_agent_safety_invariant_preserved():
    # Even if Bedrock returns LLM-tailored messages, safety bounds must NOT be relaxed
    report = load_demo_fixture()
    agent = AirDutyAgent()

    mock_llm_json = json.dumps({
        "principal_message_en": "Principal Notice: Severe pollution requires indoor schedule.",
        "parent_message_en": "Parents: Outdoor classes moved indoors today.",
        "parent_message_hi": "माता-पिता ध्यान दें: आज सभी बाहरी गतिविधियां बंद रहेंगी।"
    })

    mock_runner = MagicMock(return_value=mock_llm_json)
    agent.strands_agent = mock_runner

    response = agent.run_evaluation(report=report, sensitive_students_count=45)
    assert response.agent_mode == "bedrock_strands"
    # Invariant: PE must still be indoor_only
    assert response.pe_action == "indoor_only"
    assert response.status_level == "HAZARDOUS"
    assert "Principal Notice" in response.principal_message_en
    assert "माता-पिता" in response.parent_message_hi
