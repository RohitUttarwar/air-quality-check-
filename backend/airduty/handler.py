"""AWS Lambda entrypoints for HTTP API Gateway routes and EventBridge morning schedule, plus local dev server."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from airduty.agent import AirDutyAgent
from airduty.alerts import format_bulletin_for_sns, publish_sns_alert
from airduty.data import get_air_data, load_demo_fixture
from airduty.rules import SchoolPolicy, evaluate_school_safety
from airduty.store import (
    DEFAULT_SCHOOL_ID,
    get_decision_history,
    get_latest_decision,
    get_school_config,
    record_decision,
    save_school_config,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


def _build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Format standard API Gateway response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def execute_evaluation_workflow(
    school_id: str = DEFAULT_SCHOOL_ID,
    force_demo: bool = False,
) -> Dict[str, Any]:
    """Core evaluation loop: Data -> Rules -> Agent -> DynamoDB -> SNS Alert."""
    school = get_school_config(school_id)
    lat = float(school.get("lat", 28.6139))
    lon = float(school.get("lon", 77.2090))
    sensitive_students = int(school.get("sensitive_students_count", 45))

    # Thresholds
    thresholds_dict = school.get("policy_thresholds", {})
    policy = SchoolPolicy(**thresholds_dict) if thresholds_dict else SchoolPolicy()

    # Ingest data
    if force_demo:
        air_report = load_demo_fixture()
    else:
        air_report = get_air_data(lat=lat, lon=lon, force_demo=False)

    # Agent evaluation (with strict safety invariant + deterministic fallback)
    agent = AirDutyAgent()
    agent_response = agent.run_evaluation(
        report=air_report,
        policy=policy,
        sensitive_students_count=sensitive_students,
    )

    # Compute full decision output including activity window
    rules_decision = evaluate_school_safety(
        report=air_report,
        policy=policy,
        sensitive_students_count=sensitive_students,
    )

    decision_data = rules_decision.to_dict()
    # Overlay agent-tailored explanations
    decision_data["principal_message_en"] = agent_response.principal_message_en
    decision_data["parent_message_en"] = agent_response.parent_message_en
    decision_data["parent_message_hi"] = agent_response.parent_message_hi
    decision_data["agent_mode"] = agent_response.agent_mode
    decision_data["model_id_used"] = agent_response.model_id_used

    now_iso = datetime.now(timezone.utc).isoformat()

    # Format & dispatch SNS notification
    bulletin = format_bulletin_for_sns(decision_data, school.get("name", "School"))
    sns_result = publish_sns_alert(
        subject=f"Air Duty Directive: {rules_decision.headline} (AQI {rules_decision.current_aqi})",
        message=bulletin,
    )

    # Record audit log in DynamoDB
    record_item = {
        "timestamp": now_iso,
        "inputs": {
            "school_id": school_id,
            "lat": lat,
            "lon": lon,
            "current_pm25": air_report.current.pm25,
            "current_pm10": air_report.current.pm10,
            "is_demo": air_report.is_demo,
            "sensitive_students_count": sensitive_students,
        },
        "decision": decision_data,
        "delivery_status": sns_result.get("status"),
        "delivery_details": sns_result,
    }
    record_decision(school_id, record_item)

    return {
        "school": school,
        "air_report": air_report.to_dict(),
        "decision": decision_data,
        "delivery": sns_result,
        "timestamp": now_iso,
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Unified AWS Lambda handler for API Gateway and EventBridge scheduled events."""
    logger.info("Lambda invocation event: %s", json.dumps(event, default=str)[:300])

    # 1. EventBridge Morning Schedule Trigger (06:00 IST / 00:30 UTC)
    if event.get("source") == "aws.events" or event.get("detail-type") == "Scheduled Event":
        logger.info("Executing scheduled morning evaluation at 06:00 IST")
        result = execute_evaluation_workflow(school_id=DEFAULT_SCHOOL_ID, force_demo=False)
        return {"status": "SUCCESS", "message": "Morning evaluation completed", "result": result}

    # 2. HTTP API Request Router
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    raw_path = event.get("rawPath") or event.get("path", "/")

    # Handle CORS Preflight
    if http_method == "OPTIONS":
        return _build_response(200, {"status": "ok"})

    # Parse query parameters & body
    query_params = event.get("queryStringParameters") or {}
    body_data = {}
    if event.get("body"):
        try:
            body_data = json.loads(event["body"])
        except Exception:
            pass

    # Normalize path
    path = raw_path.rstrip("/")
    if path.startswith("/api"):
        path = path[4:]  # strip /api prefix

    try:
        # Route: POST /run (Force evaluate now)
        if http_method == "POST" and (path == "/run" or path == ""):
            demo_param = (
                str(query_params.get("demo", "")).lower() == "true"
                or bool(body_data.get("demo", False))
            )
            school_id = body_data.get("school_id") or query_params.get("school_id") or DEFAULT_SCHOOL_ID
            result = execute_evaluation_workflow(school_id=school_id, force_demo=demo_param)
            return _build_response(200, result)

        # Route: GET /status (Current dashboard status)
        elif http_method == "GET" and (path == "/status" or path == ""):
            demo_param = str(query_params.get("demo", "")).lower() == "true"
            school_id = query_params.get("school_id", DEFAULT_SCHOOL_ID)
            school = get_school_config(school_id)

            lat = float(school.get("lat", 28.6139))
            lon = float(school.get("lon", 77.2090))
            sensitive_count = int(school.get("sensitive_students_count", 45))

            if demo_param:
                air_report = load_demo_fixture()
            else:
                air_report = get_air_data(lat=lat, lon=lon, force_demo=False)

            thresholds_dict = school.get("policy_thresholds", {})
            policy = SchoolPolicy(**thresholds_dict) if thresholds_dict else SchoolPolicy()

            decision = evaluate_school_safety(
                report=air_report,
                policy=policy,
                sensitive_students_count=sensitive_count,
            )

            history = get_decision_history(school_id, limit=7)

            return _build_response(200, {
                "school": school,
                "air_report": air_report.to_dict(),
                "decision": decision.to_dict(),
                "history": history,
                "is_demo": air_report.is_demo,
            })

        # Route: GET /school
        elif http_method == "GET" and path == "/school":
            school_id = query_params.get("school_id", DEFAULT_SCHOOL_ID)
            return _build_response(200, get_school_config(school_id))

        # Route: PUT /school
        elif http_method == "PUT" and path == "/school":
            school_id = body_data.get("school_id", DEFAULT_SCHOOL_ID)
            updated = save_school_config(school_id, body_data)
            return _build_response(200, updated)

        # Route: GET /history
        elif http_method == "GET" and path == "/history":
            school_id = query_params.get("school_id", DEFAULT_SCHOOL_ID)
            limit = int(query_params.get("limit", 7))
            return _build_response(200, {"history": get_decision_history(school_id, limit=limit)})

        else:
            return _build_response(404, {"error": f"Endpoint not found: {http_method} {raw_path}"})

    except Exception as exc:
        logger.exception("Error processing request: %s", exc)
        return _build_response(500, {"error": str(exc)})


class LocalDevHandler(SimpleHTTPRequestHandler):
    """Local development HTTP request handler for instant testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve_api_lambda(self, method: str):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        # flatten single value query params
        query_params = {k: v[0] for k, v in qs.items()}

        body_data = None
        if method in ("POST", "PUT"):
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                body_data = raw_body

        event = {
            "httpMethod": method,
            "rawPath": parsed.path,
            "path": parsed.path,
            "queryStringParameters": query_params,
            "body": body_data,
        }

        resp = lambda_handler(event, None)
        body_bytes = resp["body"].encode("utf-8")

        self.send_response(resp["statusCode"])
        for k, v in resp.get("headers", {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api") or parsed.path in ("/status", "/run", "/school", "/history"):
            self._serve_api_lambda("GET")
        else:
            super().do_GET()

    def do_POST(self):
        self._serve_api_lambda("POST")

    def do_PUT(self):
        self._serve_api_lambda("PUT")



def run_local_server(port: int = 8000) -> None:
    """Run local standalone server for development and testing."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, LocalDevHandler)
    print(f"🚀 Air Duty Officer local dev server running at: http://localhost:{port}")
    print(f"📁 Serving frontend from: {FRONTEND_DIR}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dev server.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_local_server(port=port)
