"""Storage layer for Schools configuration and Decisions audit history using DynamoDB."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

DEFAULT_SCHOOL_ID = os.environ.get("DEFAULT_SCHOOL_ID", "delhi-model-school-01")
SCHOOLS_TABLE_NAME = os.environ.get("DYNAMODB_SCHOOLS_TABLE", "AirDuty_Schools")
DECISIONS_TABLE_NAME = os.environ.get("DYNAMODB_DECISIONS_TABLE", "AirDuty_Decisions")
LOCAL_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "scratch" / "data"

DEFAULT_SCHOOL_RECORD: Dict[str, Any] = {
    "school_id": DEFAULT_SCHOOL_ID,
    "name": os.environ.get("DEFAULT_SCHOOL_NAME", "Delhi Model School"),
    "lat": float(os.environ.get("DEFAULT_SCHOOL_LAT", 28.6139)),
    "lon": float(os.environ.get("DEFAULT_SCHOOL_LON", 77.2090)),
    "grade_range": os.environ.get("DEFAULT_GRADE_RANGE", "K-12"),
    "sensitive_students_count": int(os.environ.get("DEFAULT_SENSITIVE_STUDENTS", 45)),
    "contact_emails": [os.environ.get("ALERT_EMAIL", "principal@school.edu")],
    "contact_phones": ["+919876543210"],
    "policy_thresholds": {
        "pe_indoor_threshold": 201,
        "recess_indoor_threshold": 201,
        "assembly_indoor_threshold": 150,
        "mask_recommended_threshold": 150,
        "mask_mandatory_threshold": 301,
        "sensitive_trigger_threshold": 101,
        "forecast_spike_buffer": 250,
        "school_start_hour": 7,
        "school_end_hour": 15,
    },
    "updated_at": datetime.now(timezone.utc).isoformat(),
}


def _get_dynamodb_resource():
    has_creds = bool(
        os.environ.get("AWS_ACCESS_KEY_ID")
        or os.environ.get("AWS_SESSION_TOKEN")
        or os.environ.get("AWS_EXECUTION_ENV")
        or os.path.exists(os.path.expanduser("~/.aws/credentials"))
    )
    if not has_creds:
        return None

    try:
        region = os.environ.get("AWS_REGION", "ap-south-1")
        return boto3.resource("dynamodb", region_name=region)
    except Exception as exc:
        logger.debug("DynamoDB resource not available (%s); using local store", exc)
        return None


def _get_local_file_path(table_name: str) -> Path:
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return LOCAL_DATA_DIR / f"{table_name}.json"


def _read_local_table(table_name: str) -> Dict[str, Any]:
    path = _get_local_file_path(table_name)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_local_table(table_name: str, data: Dict[str, Any]) -> None:
    path = _get_local_file_path(table_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_school_config(school_id: str = DEFAULT_SCHOOL_ID) -> Dict[str, Any]:
    """Retrieve school config from DynamoDB, falling back to local store or defaults."""
    ddb = _get_dynamodb_resource()
    if ddb:
        try:
            table = ddb.Table(SCHOOLS_TABLE_NAME)
            response = table.get_item(Key={"school_id": school_id})
            item = response.get("Item")
            if item:
                # Convert Decimals to float/int if needed
                return json.loads(json.dumps(item, default=str))
        except Exception as exc:
            logger.warning("DynamoDB get_school_config error (%s); falling back to local store", exc)

    # Local fallback
    local_data = _read_local_table(SCHOOLS_TABLE_NAME)
    if school_id in local_data:
        return local_data[school_id]

    # Seed default school record in local store
    local_data[school_id] = DEFAULT_SCHOOL_RECORD
    _write_local_table(SCHOOLS_TABLE_NAME, local_data)
    return DEFAULT_SCHOOL_RECORD


def save_school_config(school_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Save or update school config."""
    current = get_school_config(school_id)
    current.update(updates)
    current["school_id"] = school_id
    current["updated_at"] = datetime.now(timezone.utc).isoformat()

    ddb = _get_dynamodb_resource()
    if ddb:
        try:
            table = ddb.Table(SCHOOLS_TABLE_NAME)
            table.put_item(Item=current)
            return current
        except Exception as exc:
            logger.warning("DynamoDB save_school_config error (%s); saving to local store", exc)

    # Local store
    local_data = _read_local_table(SCHOOLS_TABLE_NAME)
    local_data[school_id] = current
    _write_local_table(SCHOOLS_TABLE_NAME, local_data)
    return current


def record_decision(school_id: str, decision_record: Dict[str, Any]) -> Dict[str, Any]:
    """Store decision in audit history."""
    item = dict(decision_record)
    item["school_id"] = school_id
    if "timestamp" not in item:
        item["timestamp"] = datetime.now(timezone.utc).isoformat()

    ddb = _get_dynamodb_resource()
    if ddb:
        try:
            table = ddb.Table(DECISIONS_TABLE_NAME)
            table.put_item(Item=item)
            return item
        except Exception as exc:
            logger.warning("DynamoDB record_decision error (%s); recording to local store", exc)

    # Local store
    local_data = _read_local_table(DECISIONS_TABLE_NAME)
    history = local_data.get(school_id, [])
    history.insert(0, item)
    # Keep last 30
    local_data[school_id] = history[:30]
    _write_local_table(DECISIONS_TABLE_NAME, local_data)
    return item


def get_decision_history(school_id: str = DEFAULT_SCHOOL_ID, limit: int = 7) -> List[Dict[str, Any]]:
    """Retrieve the most recent decisions for a school."""
    ddb = _get_dynamodb_resource()
    if ddb:
        try:
            table = ddb.Table(DECISIONS_TABLE_NAME)
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("school_id").eq(school_id),
                ScanIndexForward=False,
                Limit=limit,
            )
            items = response.get("Items", [])
            if items:
                return json.loads(json.dumps(items, default=str))
        except Exception as exc:
            logger.warning("DynamoDB get_decision_history query error (%s); reading from local store", exc)

    # Local store
    local_data = _read_local_table(DECISIONS_TABLE_NAME)
    history = local_data.get(school_id, [])
    return history[:limit]


def get_latest_decision(school_id: str = DEFAULT_SCHOOL_ID) -> Optional[Dict[str, Any]]:
    """Get the latest recorded decision."""
    history = get_decision_history(school_id=school_id, limit=1)
    return history[0] if history else None
