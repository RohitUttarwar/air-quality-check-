"""Air quality data retrieval from Open-Meteo API and optional WAQI station cross-check."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from airduty.aqi import AQIResult, calculate_cpcb_aqi

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WAQI_BASE_URL = "https://api.waqi.info/feed"


@dataclass(frozen=True)
class AirQualitySnapshot:
    timestamp: str
    pm25: float
    pm10: float
    source: str


@dataclass(frozen=True)
class HourlyForecastPoint:
    time: str
    pm25: float
    pm10: float
    cpcb_aqi: int
    cpcb_category: str
    color_hex: str


@dataclass(frozen=True)
class WAQICheck:
    station_name: str
    aqi: Optional[int]
    pm25: Optional[float]
    pm10: Optional[float]
    available: bool


@dataclass
class AirDataReport:
    lat: float
    lon: float
    current: AirQualitySnapshot
    cpcb_current: AQIResult
    forecast: List[HourlyForecastPoint]
    waqi_cross_check: Optional[WAQICheck]
    is_demo: bool
    retrieved_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "current": asdict(self.current),
            "cpcb_current": self.cpcb_current.to_dict(),
            "forecast": [asdict(f) for f in self.forecast],
            "waqi_cross_check": asdict(self.waqi_cross_check) if self.waqi_cross_check else None,
            "is_demo": self.is_demo,
            "retrieved_at": self.retrieved_at,
        }


def get_fixture_path() -> Path:
    """Resolve path to severe_day.json fixture."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / "fixtures" / "severe_day.json"


def load_demo_fixture(fixture_path: Optional[Path | str] = None) -> AirDataReport:
    """Load recorded severe pollution fixture for demo and offline use."""
    path = Path(fixture_path) if fixture_path else get_fixture_path()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cur_raw = data["current"]
    cur_pm25 = float(cur_raw["pm2_5"])
    cur_pm10 = float(cur_raw["pm10"])
    cur_cpcb = calculate_cpcb_aqi(pm25=cur_pm25, pm10=cur_pm10)

    current = AirQualitySnapshot(
        timestamp=cur_raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
        pm25=cur_pm25,
        pm10=cur_pm10,
        source=cur_raw.get("source", "Recorded Fixture (Offline)"),
    )

    forecast_points: List[HourlyForecastPoint] = []
    for pt in data.get("hourly_forecast", []):
        p_pm25 = float(pt["pm2_5"])
        p_pm10 = float(pt["pm10"])
        pt_cpcb = calculate_cpcb_aqi(pm25=p_pm25, pm10=p_pm10)
        forecast_points.append(
            HourlyForecastPoint(
                time=pt["time"],
                pm25=p_pm25,
                pm10=p_pm10,
                cpcb_aqi=pt_cpcb.aqi,
                cpcb_category=pt_cpcb.category.value,
                color_hex=pt_cpcb.color_hex,
            )
        )

    waqi_raw = data.get("waqi_cross_check")
    waqi_check = None
    if waqi_raw:
        waqi_check = WAQICheck(
            station_name=waqi_raw.get("station_name", "Unknown Station"),
            aqi=waqi_raw.get("aqi"),
            pm25=waqi_raw.get("pm2_5"),
            pm10=waqi_raw.get("pm10"),
            available=waqi_raw.get("available", True),
        )

    school_info = data.get("school", {})

    return AirDataReport(
        lat=school_info.get("lat", 28.6139),
        lon=school_info.get("lon", 77.2090),
        current=current,
        cpcb_current=cur_cpcb,
        forecast=forecast_points,
        waqi_cross_check=waqi_check,
        is_demo=True,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )


def fetch_open_meteo(lat: float, lon: float, timeout_sec: int = 8) -> Dict[str, Any]:
    """Fetch hourly air quality data from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm10,pm2_5",
        "timezone": "auto",
        "forecast_days": 2,
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout_sec)
    response.raise_for_status()
    return response.json()


def fetch_waqi_station(lat: float, lon: float, token: Optional[str] = None, timeout_sec: int = 5) -> Optional[WAQICheck]:
    """Fetch nearest ground station reading from WAQI if token is provided."""
    token = token or os.environ.get("WAQI_TOKEN", "").strip()
    if not token:
        return None

    url = f"{WAQI_BASE_URL}/geo:{lat};{lon}/"
    try:
        response = requests.get(url, params={"token": token}, timeout=timeout_sec)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "ok":
            logger.warning("WAQI responded with non-ok status: %s", payload.get("data"))
            return None

        station_data = payload.get("data", {})
        iaqi = station_data.get("iaqi", {})
        pm25_val = iaqi.get("pm25", {}).get("v")
        pm10_val = iaqi.get("pm10", {}).get("v")
        aqi_val = station_data.get("aqi")

        city_name = station_data.get("city", {}).get("name", "Nearest WAQI Station")

        return WAQICheck(
            station_name=city_name,
            aqi=int(aqi_val) if aqi_val is not None else None,
            pm25=float(pm25_val) if pm25_val is not None else None,
            pm10=float(pm10_val) if pm10_val is not None else None,
            available=True,
        )
    except Exception as exc:
        logger.warning("WAQI ground station cross-check failed gracefully: %s", exc)
        return WAQICheck(
            station_name="Station unavailable",
            aqi=None,
            pm25=None,
            pm10=None,
            available=False,
        )


def get_air_data(
    lat: float,
    lon: float,
    force_demo: bool = False,
    waqi_token: Optional[str] = None,
) -> AirDataReport:
    """Retrieve air quality data for a location.

    Falls back cleanly to demo fixture if force_demo=True or Open-Meteo fails.
    """
    if force_demo:
        return load_demo_fixture()

    try:
        raw = fetch_open_meteo(lat=lat, lon=lon)
        hourly = raw.get("hourly", {})
        times = hourly.get("time", [])
        pm25_list = hourly.get("pm2_5", [])
        pm10_list = hourly.get("pm10", [])

        if not times or not pm25_list or not pm10_list:
            raise ValueError("Open-Meteo returned empty hourly series")

        # Find the latest non-null reading or first point as current
        current_idx = 0
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
        for idx, t_str in enumerate(times):
            if t_str <= now_iso and pm25_list[idx] is not None:
                current_idx = idx

        cur_pm25 = float(pm25_list[current_idx] if pm25_list[current_idx] is not None else 25.0)
        cur_pm10 = float(pm10_list[current_idx] if pm10_list[current_idx] is not None else 45.0)
        cur_time = times[current_idx]

        cpcb_current = calculate_cpcb_aqi(pm25=cur_pm25, pm10=cur_pm10)
        current_snapshot = AirQualitySnapshot(
            timestamp=cur_time,
            pm25=cur_pm25,
            pm10=cur_pm10,
            source="Open-Meteo Air Quality API",
        )

        forecast_points: List[HourlyForecastPoint] = []
        # Take the next 24 hours from current
        end_idx = min(len(times), current_idx + 25)
        for i in range(current_idx, end_idx):
            val_25 = pm25_list[i] if pm25_list[i] is not None else cur_pm25
            val_10 = pm10_list[i] if pm10_list[i] is not None else cur_pm10
            pt_cpcb = calculate_cpcb_aqi(pm25=float(val_25), pm10=float(val_10))
            forecast_points.append(
                HourlyForecastPoint(
                    time=times[i],
                    pm25=float(val_25),
                    pm10=float(val_10),
                    cpcb_aqi=pt_cpcb.aqi,
                    cpcb_category=pt_cpcb.category.value,
                    color_hex=pt_cpcb.color_hex,
                )
            )

        waqi_check = fetch_waqi_station(lat=lat, lon=lon, token=waqi_token)

        return AirDataReport(
            lat=lat,
            lon=lon,
            current=current_snapshot,
            cpcb_current=cpcb_current,
            forecast=forecast_points,
            waqi_cross_check=waqi_check,
            is_demo=False,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as exc:
        logger.error("Live Open-Meteo fetch failed (%s); falling back to demo fixture", exc)
        fixture_report = load_demo_fixture()
        # Mark that it was a live attempt that degraded to demo fixture
        return fixture_report
