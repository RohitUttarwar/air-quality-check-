"""Unit tests for Lambda handlers, store, and alerts."""

import json
from unittest.mock import MagicMock, patch
import pytest

from airduty.alerts import format_bulletin_for_sns, publish_sns_alert
from airduty.handler import lambda_handler
from airduty.store import (
    get_decision_history,
    get_school_config,
    record_decision,
    save_school_config,
)


def test_store_school_config_crud():
    school = get_school_config("test-school-1")
    assert school["name"] is not None
    assert "policy_thresholds" in school

    # Update
    updated = save_school_config("test-school-1", {"name": "Test Academy", "sensitive_students_count": 55})
    assert updated["name"] == "Test Academy"
    assert updated["sensitive_students_count"] == 55

    # Fetch again
    fetched = get_school_config("test-school-1")
    assert fetched["name"] == "Test Academy"


def test_store_decision_history():
    item = {
        "timestamp": "2026-11-15T06:00:00Z",
        "decision": {"headline": "Test Decision", "current_aqi": 320},
    }
    record_decision("test-school-1", item)
    history = get_decision_history("test-school-1", limit=5)
    assert len(history) >= 1
    assert history[0]["decision"]["headline"] == "Test Decision"


def test_alerts_formatting_and_publish():
    decision_mock = {
        "headline": "Keep PE Indoors",
        "current_aqi": 412,
        "current_category": "Severe",
        "pe_action": "indoor_only",
        "assembly_action": "indoor_only",
        "recess_action": "indoor_only",
        "mask_advisory": "mandatory_all",
        "ventilation_advice": "air_purifiers_active",
        "reasons": ["AQI exceeds 400", "Winter inversion episode"],
        "parent_message_en": "Keep safe indoors.",
        "parent_message_hi": "कृपया घर पर रहें।",
    }
    bulletin = format_bulletin_for_sns(decision_mock, "Delhi Model School")
    assert "AIR DUTY OFFICER" in bulletin
    assert "Severe" in bulletin
    assert "कृपया घर पर रहें" in bulletin

    # Publish simulated alert (empty ARN)
    res = publish_sns_alert("Air Duty Notice", bulletin, topic_arn="")
    assert res["status"] == "SIMULATED_LOCAL"


def test_handler_get_status_demo():
    event = {
        "httpMethod": "GET",
        "rawPath": "/status",
        "queryStringParameters": {"demo": "true"},
    }
    resp = lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["is_demo"] is True
    assert body["decision"]["status_level"] == "HAZARDOUS"


def test_handler_post_run_demo():
    event = {
        "httpMethod": "POST",
        "rawPath": "/run",
        "body": json.dumps({"demo": True}),
    }
    resp = lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "decision" in body
    assert "delivery" in body
    assert body["air_report"]["is_demo"] is True


def test_handler_school_routes():
    # PUT /school
    put_event = {
        "httpMethod": "PUT",
        "rawPath": "/school",
        "body": json.dumps({"name": "Green Valley International", "sensitive_students_count": 60}),
    }
    put_resp = lambda_handler(put_event, None)
    assert put_resp["statusCode"] == 200
    put_body = json.loads(put_resp["body"])
    assert put_body["name"] == "Green Valley International"

    # GET /school
    get_event = {
        "httpMethod": "GET",
        "rawPath": "/school",
    }
    get_resp = lambda_handler(get_event, None)
    assert get_resp["statusCode"] == 200
    get_body = json.loads(get_resp["body"])
    assert get_body["name"] == "Green Valley International"


def test_handler_get_history():
    event = {
        "httpMethod": "GET",
        "rawPath": "/history",
    }
    resp = lambda_handler(event, None)
    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "history" in body
    assert isinstance(body["history"], list)


def test_handler_eventbridge_scheduled_invocation():
    event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
    }
    resp = lambda_handler(event, None)
    assert resp["status"] == "SUCCESS"
    assert "result" in resp
