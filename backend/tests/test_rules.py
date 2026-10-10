"""Unit tests for deterministic school safety rules engine."""

import pytest
from airduty.aqi import calculate_cpcb_aqi
from airduty.data import AirDataReport, AirQualitySnapshot, HourlyForecastPoint
from airduty.rules import (
    SchoolPolicy,
    evaluate_school_safety,
    find_best_outdoor_window,
)


def make_dummy_report(
    pm25: float,
    pm10: float,
    forecast_pm25: float | None = None,
) -> AirDataReport:
    cpcb = calculate_cpcb_aqi(pm25=pm25, pm10=pm10)
    snap = AirQualitySnapshot(
        timestamp="2026-11-15T06:00",
        pm25=pm25,
        pm10=pm10,
        source="Test Mock",
    )
    f_pm = forecast_pm25 if forecast_pm25 is not None else pm25
    forecast = [
        HourlyForecastPoint(
            time=f"2026-11-15T{hour:02d}:00",
            pm25=f_pm,
            pm10=pm10,
            cpcb_aqi=cpcb.aqi,
            cpcb_category=cpcb.category.value,
            color_hex=cpcb.color_hex,
        )
        for hour in range(6, 18)
    ]
    return AirDataReport(
        lat=28.6139,
        lon=77.2090,
        current=snap,
        cpcb_current=cpcb,
        forecast=forecast,
        waqi_cross_check=None,
        is_demo=False,
        retrieved_at="2026-11-15T06:00:00Z",
    )


def test_rules_good_day():
    rep = make_dummy_report(pm25=15.0, pm10=25.0)  # AQI 25 Good
    decision = evaluate_school_safety(rep, sensitive_students_count=0)
    assert decision.status_level == "SAFE"
    assert decision.pe_action == "allow_outdoor"
    assert decision.assembly_action == "allow_outdoor"
    assert decision.mask_advisory == "none"
    assert decision.ventilation_advice == "open_windows"
    assert "Safe" in decision.headline


def test_rules_moderate_day_with_sensitive_students():
    rep = make_dummy_report(pm25=75.0, pm10=140.0)  # AQI ~151 Moderate
    decision = evaluate_school_safety(rep, sensitive_students_count=20)
    assert decision.status_level == "CAUTION"
    assert decision.pe_action == "restricted_intensity"
    assert "20 students" in decision.sensitive_students_notice
    assert decision.mask_advisory == "recommended_sensitive"


def test_rules_poor_day():
    rep = make_dummy_report(pm25=105.0, pm10=280.0)  # AQI ~251 Poor
    decision = evaluate_school_safety(rep, sensitive_students_count=5)
    assert decision.status_level == "RESTRICTED"
    assert decision.pe_action == "indoor_only"
    assert decision.assembly_action == "indoor_only"
    assert decision.ventilation_advice == "air_purifiers_active"


def test_rules_severe_day():
    rep = make_dummy_report(pm25=315.0, pm10=460.0)  # AQI > 400 Severe
    decision = evaluate_school_safety(rep, sensitive_students_count=45)
    assert decision.status_level == "HAZARDOUS"
    assert decision.pe_action == "indoor_only"
    assert decision.assembly_action == "indoor_only"
    assert decision.mask_advisory == "mandatory_all"
    assert "45 sensitive students" in decision.reasons[2]
    assert "अभिभावक ध्यान दें" in decision.parent_message_hi


def test_rules_forecast_spike_preventive_action():
    # Current is Satisfactory (pm25=45 -> AQI 76), but next 6 hours spike to 260
    base_rep = make_dummy_report(pm25=45.0, pm10=80.0)
    # Inject a spike at hour 9
    spiked_forecast = list(base_rep.forecast)
    spiked_cpcb = calculate_cpcb_aqi(pm25=260.0, pm10=450.0)
    spiked_forecast[3] = HourlyForecastPoint(
        time="2026-11-15T09:00",
        pm25=260.0,
        pm10=450.0,
        cpcb_aqi=spiked_cpcb.aqi,
        cpcb_category=spiked_cpcb.category.value,
        color_hex=spiked_cpcb.color_hex,
    )
    base_rep.forecast = spiked_forecast

    decision = evaluate_school_safety(base_rep)
    # Should proactively force PE indoor because peak forecast AQI >= 250
    assert decision.pe_action == "indoor_only"
    assert decision.assembly_action == "indoor_only"


def test_find_best_outdoor_window():
    # Construct forecast with a dipping valley between 12:00 and 14:00
    points = [
        HourlyForecastPoint(time="2026-11-15T08:00", pm25=300.0, pm10=400.0, cpcb_aqi=400, cpcb_category="Severe", color_hex="#7E0023"),
        HourlyForecastPoint(time="2026-11-15T09:00", pm25=280.0, pm10=390.0, cpcb_aqi=380, cpcb_category="Very Poor", color_hex="#E53935"),
        HourlyForecastPoint(time="2026-11-15T10:00", pm25=240.0, pm10=350.0, cpcb_aqi=350, cpcb_category="Very Poor", color_hex="#E53935"),
        HourlyForecastPoint(time="2026-11-15T11:00", pm25=210.0, pm10=320.0, cpcb_aqi=320, cpcb_category="Very Poor", color_hex="#E53935"),
        HourlyForecastPoint(time="2026-11-15T12:00", pm25=150.0, pm10=250.0, cpcb_aqi=250, cpcb_category="Poor", color_hex="#FF7E00"),
        HourlyForecastPoint(time="2026-11-15T13:00", pm25=145.0, pm10=240.0, cpcb_aqi=240, cpcb_category="Poor", color_hex="#FF7E00"),
        HourlyForecastPoint(time="2026-11-15T14:00", pm25=190.0, pm10=290.0, cpcb_aqi=290, cpcb_category="Poor", color_hex="#FF7E00"),
    ]
    window = find_best_outdoor_window(points, start_hour=8, end_hour=14)
    assert window is not None
    assert window.start_time == "2026-11-15T12:00"
    assert window.end_time == "2026-11-15T13:00"
    assert window.avg_pm25 == 147.5
