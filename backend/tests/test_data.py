"""Unit tests for air quality data fetching and fixtures."""

from unittest.mock import patch
import pytest
import requests

from airduty.aqi import AQICategory
from airduty.data import (
    AirDataReport,
    fetch_waqi_station,
    get_air_data,
    load_demo_fixture,
)


def test_load_demo_fixture():
    report = load_demo_fixture()
    assert report.is_demo is True
    assert report.current.pm25 > 300.0  # Severe day
    assert report.cpcb_current.category == AQICategory.SEVERE
    assert len(report.forecast) == 24
    assert report.waqi_cross_check is not None
    assert report.waqi_cross_check.available is True
    assert report.waqi_cross_check.aqi == 448


def test_waqi_station_without_token():
    # When WAQI_TOKEN is unset or empty, should return None without error
    check = fetch_waqi_station(lat=28.6139, lon=77.2090, token="")
    assert check is None


@patch("airduty.data.requests.get")
def test_waqi_station_network_failure(mock_get):
    mock_get.side_effect = requests.RequestException("Connection timeout")
    check = fetch_waqi_station(lat=28.6139, lon=77.2090, token="mock-token-xyz")
    assert check is not None
    assert check.available is False
    assert check.aqi is None


@patch("airduty.data.fetch_open_meteo")
def test_get_air_data_fallback_on_api_error(mock_fetch):
    # If Open-Meteo throws, get_air_data should gracefully degrade to fixture
    mock_fetch.side_effect = requests.RequestException("API Down")
    report = get_air_data(lat=28.6139, lon=77.2090, force_demo=False)
    assert report is not None
    assert report.is_demo is True
    assert report.cpcb_current.category == AQICategory.SEVERE


def test_get_air_data_force_demo():
    report = get_air_data(lat=28.6139, lon=77.2090, force_demo=True)
    assert report.is_demo is True
    assert report.cpcb_current.category == AQICategory.SEVERE
