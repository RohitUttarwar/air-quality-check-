"""CPCB National Air Quality Index (NAQI) calculation module.

Reference:
Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change,
Government of India - "National Air Quality Index" (2014-2015 Technical Guidelines).
Breakpoints follow the official Indian standard for PM2.5 and PM10 24-hour averages.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class AQICategory(str, Enum):
    GOOD = "Good"
    SATISFACTORY = "Satisfactory"
    MODERATE = "Moderate"
    POOR = "Poor"
    VERY_POOR = "Very Poor"
    SEVERE = "Severe"


# Category metadata with standard CPCB visual colors
CATEGORY_DETAILS: Dict[AQICategory, Dict[str, str]] = {
    AQICategory.GOOD: {
        "color": "#00B050",  # Green
        "description": "Minimal impact. Clean and safe for all outdoor activities.",
    },
    AQICategory.SATISFACTORY: {
        "color": "#92D050",  # Light Green
        "description": "Minor breathing discomfort to sensitive people.",
    },
    AQICategory.MODERATE: {
        "color": "#E5A93B",  # Yellow/Amber
        "description": "Breathing discomfort to people with lung disease, asthma, and heart diseases.",
    },
    AQICategory.POOR: {
        "color": "#FF7E00",  # Orange
        "description": "Breathing discomfort to most people on prolonged outdoor exposure.",
    },
    AQICategory.VERY_POOR: {
        "color": "#E53935",  # Red
        "description": "Respiratory illness on prolonged exposure. Pronounced impact on children.",
    },
    AQICategory.SEVERE: {
        "color": "#7E0023",  # Deep Maroon/Purple
        "description": "Affects healthy people and seriously impacts those with existing diseases.",
    },
}

# CPCB Breakpoints: (B_lo, B_hi, I_lo, I_hi, Category)
# Formula: I = I_lo + ((I_hi - I_lo) / (B_hi - B_lo)) * (C - B_lo)
PM25_BREAKPOINTS: List[Tuple[float, float, int, int, AQICategory]] = [
    (0.0, 30.0, 0, 50, AQICategory.GOOD),
    (30.0, 60.0, 51, 100, AQICategory.SATISFACTORY),
    (60.0, 90.0, 101, 200, AQICategory.MODERATE),
    (90.0, 120.0, 201, 300, AQICategory.POOR),
    (120.0, 250.0, 301, 400, AQICategory.VERY_POOR),
    (250.0, 380.0, 401, 500, AQICategory.SEVERE),
]

PM10_BREAKPOINTS: List[Tuple[float, float, int, int, AQICategory]] = [
    (0.0, 50.0, 0, 50, AQICategory.GOOD),
    (50.0, 100.0, 51, 100, AQICategory.SATISFACTORY),
    (100.0, 250.0, 101, 200, AQICategory.MODERATE),
    (250.0, 350.0, 201, 300, AQICategory.POOR),
    (350.0, 430.0, 301, 400, AQICategory.VERY_POOR),
    (430.0, 500.0, 401, 500, AQICategory.SEVERE),
]


@dataclass(frozen=True)
class AQIResult:
    aqi: int
    category: AQICategory
    pm25_sub_index: Optional[int]
    pm10_sub_index: Optional[int]
    pm25_value: Optional[float]
    pm10_value: Optional[float]
    dominant_pollutant: str
    color_hex: str
    description: str

    def to_dict(self) -> dict:
        return {
            "aqi": self.aqi,
            "category": self.category.value,
            "pm25_sub_index": self.pm25_sub_index,
            "pm10_sub_index": self.pm10_sub_index,
            "pm25_value": self.pm25_value,
            "pm10_value": self.pm10_value,
            "dominant_pollutant": self.dominant_pollutant,
            "color_hex": self.color_hex,
            "description": self.description,
        }


def calculate_sub_index(concentration: Optional[float], pollutant: str) -> Optional[int]:
    """Calculate the CPCB sub-index for a single pollutant using linear interpolation.

    Args:
        concentration: Pollutant concentration in µg/m³.
        pollutant: 'pm2_5' or 'pm10'.

    Returns:
        Integer sub-index (0 to 500+), or None if concentration is invalid.
    """
    if concentration is None or concentration < 0:
        return None

    breakpoints = PM25_BREAKPOINTS if pollutant == "pm2_5" else PM10_BREAKPOINTS

    # If concentration exceeds the highest defined range, interpolate above 500
    last_b_lo, last_b_hi, last_i_lo, last_i_hi, _ = breakpoints[-1]
    if concentration >= last_b_hi:
        slope = (last_i_hi - last_i_lo) / (last_b_hi - last_b_lo)
        sub_index = last_i_hi + (concentration - last_b_hi) * slope
        return int(math.floor(sub_index + 0.5))

    # Standard linear interpolation within breakpoint brackets
    for b_lo, b_hi, i_lo, i_hi, _ in breakpoints:
        if b_lo <= concentration <= b_hi:
            if math.isclose(b_hi, b_lo):
                return i_lo
            slope = (i_hi - i_lo) / (b_hi - b_lo)
            sub_index = i_lo + (concentration - b_lo) * slope
            return int(math.floor(sub_index + 0.5))

    return None


def get_category_for_aqi(aqi: int) -> AQICategory:
    """Map an AQI integer value to the corresponding official CPCB category."""
    if aqi <= 50:
        return AQICategory.GOOD
    elif aqi <= 100:
        return AQICategory.SATISFACTORY
    elif aqi <= 200:
        return AQICategory.MODERATE
    elif aqi <= 300:
        return AQICategory.POOR
    elif aqi <= 400:
        return AQICategory.VERY_POOR
    else:
        return AQICategory.SEVERE


def compute_cpcb_aqi(
    pm25: Optional[float] = None,
    pm10: Optional[float] = None,
) -> AQIResult:
    """Compute the overall CPCB AQI as the worst (maximum) sub-index.

    Args:
        pm25: PM2.5 concentration in µg/m³.
        pm10: PM10 concentration in µg/m³.

    Returns:
        AQIResult containing the overall AQI, category, and pollutant breakdowns.
    """
    pm25_sub = calculate_sub_index(pm25, "pm2_5") if pm25 is not None else None
    pm10_sub = calculate_sub_index(pm10, "pm10") if pm10 is not None else None

    if pm25_sub is None and pm10_sub is None:
        raise ValueError("At least one valid pollutant concentration (PM2.5 or PM10) must be provided.")

    if pm25_sub is not None and pm10_sub is not None:
        if pm25_sub > pm10_sub:
            overall_aqi = pm25_sub
            dominant = "pm2_5"
        elif pm10_sub > pm25_sub:
            overall_aqi = pm10_sub
            dominant = "pm10"
        else:
            overall_aqi = pm25_sub
            dominant = "both"
    elif pm25_sub is not None:
        overall_aqi = pm25_sub
        dominant = "pm2_5"
    else:
        assert pm10_sub is not None
        overall_aqi = pm10_sub
        dominant = "pm10"

    category = get_category_for_aqi(overall_aqi)
    meta = CATEGORY_DETAILS[category]

    return AQIResult(
        aqi=overall_aqi,
        category=category,
        pm25_sub_index=pm25_sub,
        pm10_sub_index=pm10_sub,
        pm25_value=pm25,
        pm10_value=pm10,
        dominant_pollutant=dominant,
        color_hex=meta["color"],
        description=meta["description"],
    )


# Alias for compatibility with various naming conventions
calculate_cpcb_aqi = compute_cpcb_aqi
