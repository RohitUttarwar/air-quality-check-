"""Unit tests for CPCB AQI sub-index calculation and categories."""

import pytest
from airduty.aqi import (
    AQICategory,
    calculate_cpcb_aqi,
    calculate_sub_index,
    get_category_for_aqi,
)


def test_sub_index_good_range():
    # PM2.5 = 15 µg/m³ -> 15/30 * 50 = 25
    idx = calculate_sub_index(15.0, "pm2_5")
    assert idx == 25

    # PM10 = 25 µg/m³ -> 25/50 * 50 = 25
    idx10 = calculate_sub_index(25.0, "pm10")
    assert idx10 == 25


def test_sub_index_satisfactory_range():
    # PM2.5 = 45 -> 51 + (49 / 30) * 15 = 51 + 24.5 = 76 (rounded)
    idx = calculate_sub_index(45.0, "pm2_5")
    assert idx == 76

    # PM10 = 75 -> 51 + (49 / 50) * 25 = 51 + 24.5 = 76
    idx10 = calculate_sub_index(75.0, "pm10")
    assert idx10 == 76


def test_sub_index_moderate_range():
    # PM2.5 = 75 -> 101 + (99 / 30) * 15 = 101 + 49.5 = 151 (rounded)
    idx = calculate_sub_index(75.0, "pm2_5")
    assert idx == 151


def test_sub_index_poor_range():
    # PM2.5 = 105 -> 201 + (99 / 30) * 15 = 201 + 49.5 = 251 (rounded)
    idx = calculate_sub_index(105.0, "pm2_5")
    assert idx == 251


def test_sub_index_very_poor_range():
    # PM2.5 = 185 -> 301 + (99 / 130) * 65 = 301 + 49.5 = 351 (rounded)
    idx = calculate_sub_index(185.0, "pm2_5")
    assert idx == 351


def test_sub_index_severe_range():
    # PM2.5 = 300 -> 401 + (99 / 130) * 50 = 401 + 38 = 439
    idx = calculate_sub_index(300.0, "pm2_5")
    assert idx == 439


def test_sub_index_beyond_scale():
    # Extreme pollution (e.g., Delhi winter peak 500 µg/m³)
    idx = calculate_sub_index(500.0, "pm2_5")
    assert idx > 500


def test_compute_cpcb_aqi_worst_sub_index():
    # PM2.5 is Good (15 -> 25), PM10 is Very Poor (390 -> 351)
    res = calculate_cpcb_aqi(pm25=15.0, pm10=390.0)
    assert res.category == AQICategory.VERY_POOR
    assert res.aqi == 351
    assert res.dominant_pollutant == "pm10"
    assert res.pm25_sub_index == 25
    assert res.pm10_sub_index == 351


def test_compute_cpcb_aqi_pm25_dominates():
    # PM2.5 is Severe (300 -> 439), PM10 is Moderate (150 -> 134)
    res = calculate_cpcb_aqi(pm25=300.0, pm10=150.0)
    assert res.category == AQICategory.SEVERE
    assert res.aqi == 439
    assert res.dominant_pollutant == "pm2_5"


def test_single_pollutant_pm25():
    res = calculate_cpcb_aqi(pm25=25.0, pm10=None)
    assert res.category == AQICategory.GOOD
    assert res.pm10_sub_index is None
    assert res.dominant_pollutant == "pm2_5"


def test_single_pollutant_pm10():
    res = calculate_cpcb_aqi(pm25=None, pm10=80.0)
    assert res.category == AQICategory.SATISFACTORY
    assert res.pm25_sub_index is None
    assert res.dominant_pollutant == "pm10"


def test_no_pollutant_raises_error():
    with pytest.raises(ValueError):
        calculate_cpcb_aqi(pm25=None, pm10=None)


def test_category_thresholds():
    assert get_category_for_aqi(45) == AQICategory.GOOD
    assert get_category_for_aqi(50) == AQICategory.GOOD
    assert get_category_for_aqi(51) == AQICategory.SATISFACTORY
    assert get_category_for_aqi(100) == AQICategory.SATISFACTORY
    assert get_category_for_aqi(101) == AQICategory.MODERATE
    assert get_category_for_aqi(200) == AQICategory.MODERATE
    assert get_category_for_aqi(201) == AQICategory.POOR
    assert get_category_for_aqi(300) == AQICategory.POOR
    assert get_category_for_aqi(301) == AQICategory.VERY_POOR
    assert get_category_for_aqi(400) == AQICategory.VERY_POOR
    assert get_category_for_aqi(401) == AQICategory.SEVERE
    assert get_category_for_aqi(600) == AQICategory.SEVERE
