"""Deterministic School Safety Rules Engine.

Evaluates air quality telemetry, 24h forecasts, and school-specific policy thresholds
to compute actionable operational decisions (PE, Assembly, Recess, Masks, Ventilation)
with complete fallback message templates in English and Hindi.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from airduty.aqi import AQICategory, AQIResult
from airduty.data import AirDataReport, HourlyForecastPoint


@dataclass
class SchoolPolicy:
    """Configurable school thresholds.

    NOTE: Marked as editable defaults, not statutory government rules.
    Schools may adjust based on indoor infrastructure, air purifiers, or local guidelines.
    """
    pe_indoor_threshold: int = 201          # AQI >= 201 (Poor) -> PE indoors
    recess_indoor_threshold: int = 201      # AQI >= 201 (Poor) -> Recess indoors
    assembly_indoor_threshold: int = 150    # AQI >= 150 (Moderate+) -> Assembly indoors
    mask_recommended_threshold: int = 150   # AQI >= 150 -> Recommended for sensitive
    mask_mandatory_threshold: int = 301     # AQI >= 301 (Very Poor+) -> Mandatory for all
    sensitive_trigger_threshold: int = 101  # AQI >= 101 -> Alert for asthmatic/sensitive students
    forecast_spike_buffer: int = 250        # Forecast spike trigger within 6 school hours
    school_start_hour: int = 7              # 07:00
    school_end_hour: int = 15               # 15:00

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActivityWindow:
    start_time: str
    end_time: str
    avg_pm25: float
    reason: str


@dataclass
class DecisionOutput:
    headline: str
    status_level: str  # "SAFE", "CAUTION", "RESTRICTED", "HAZARDOUS"
    pe_action: str     # "allow_outdoor", "indoor_only", "restricted_intensity"
    recess_action: str # "allow_outdoor", "indoor_only", "sheltered_only"
    assembly_action: str # "allow_outdoor", "indoor_only"
    mask_advisory: str # "none", "recommended_sensitive", "mandatory_all"
    ventilation_advice: str # "open_windows", "close_windows", "air_purifiers_active"
    sensitive_students_notice: str
    best_window: Optional[ActivityWindow]
    reasons: List[str]
    principal_message_en: str
    parent_message_en: str
    parent_message_hi: str
    applied_policy: Dict[str, Any]
    current_aqi: int
    current_category: str
    peak_forecast_aqi: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.best_window:
            d["best_window"] = asdict(self.best_window)
        return d


def find_best_outdoor_window(
    forecast: List[HourlyForecastPoint],
    start_hour: int = 7,
    end_hour: int = 15,
) -> Optional[ActivityWindow]:
    """Find the cleanest consecutive 2-hour window during school hours."""
    school_points: List[HourlyForecastPoint] = []
    for pt in forecast:
        try:
            # Parse hour from ISO string e.g. "2026-11-15T09:00"
            hour = int(pt.time.split("T")[1].split(":")[0])
            if start_hour <= hour <= end_hour:
                school_points.append(pt)
        except Exception:
            continue

    if len(school_points) < 2:
        return None

    best_start_idx = 0
    best_avg_pm = float("inf")

    for i in range(len(school_points) - 1):
        avg_pm = (school_points[i].pm25 + school_points[i + 1].pm25) / 2.0
        if avg_pm < best_avg_pm:
            best_avg_pm = avg_pm
            best_start_idx = i

    p1 = school_points[best_start_idx]
    p2 = school_points[best_start_idx + 1]

    return ActivityWindow(
        start_time=p1.time,
        end_time=p2.time,
        avg_pm25=round(best_avg_pm, 1),
        reason=f"Lowest PM2.5 period during school day (~{round(best_avg_pm, 1)} µg/m³)",
    )


def evaluate_school_safety(
    report: AirDataReport,
    policy: Optional[SchoolPolicy] = None,
    sensitive_students_count: int = 0,
) -> DecisionOutput:
    """Evaluate deterministic safety rules.

    Pure Python logic: guarantees 100% reproducible decisions regardless of LLM availability.
    """
    if policy is None:
        policy = SchoolPolicy()

    current_aqi = report.cpcb_current.aqi
    cat = report.cpcb_current.category

    # Check next 6 hours for forecast peak
    lookahead = report.forecast[:6] if report.forecast else []
    peak_forecast_aqi = max([pt.cpcb_aqi for pt in lookahead], default=current_aqi)
    peak_forecast_pm25 = max([pt.pm25 for pt in lookahead], default=report.current.pm25)

    forecast_spike = peak_forecast_aqi >= policy.forecast_spike_buffer

    # Determine PE Action
    if current_aqi >= policy.pe_indoor_threshold or forecast_spike:
        pe_action = "indoor_only"
    elif current_aqi >= 101:
        pe_action = "restricted_intensity"
    else:
        pe_action = "allow_outdoor"

    # Determine Recess Action
    if current_aqi >= policy.recess_indoor_threshold:
        recess_action = "indoor_only"
    elif current_aqi >= 150:
        recess_action = "sheltered_only"
    else:
        recess_action = "allow_outdoor"

    # Determine Assembly Action
    if current_aqi >= policy.assembly_indoor_threshold or forecast_spike:
        assembly_action = "indoor_only"
    else:
        assembly_action = "allow_outdoor"

    # Determine Mask Advisory
    if current_aqi >= policy.mask_mandatory_threshold or peak_forecast_aqi >= policy.mask_mandatory_threshold:
        mask_advisory = "mandatory_all"
    elif current_aqi >= policy.mask_recommended_threshold:
        mask_advisory = "recommended_sensitive"
    else:
        mask_advisory = "none"

    # Determine Ventilation Advice
    if current_aqi >= 201:
        ventilation_advice = "air_purifiers_active"
    elif current_aqi >= 101:
        ventilation_advice = "close_windows"
    else:
        ventilation_advice = "open_windows"

    # Sensitive Students Notice
    if sensitive_students_count > 0 and current_aqi >= policy.sensitive_trigger_threshold:
        sensitive_students_notice = (
            f"Active precaution for {sensitive_students_count} students with known respiratory conditions. "
            "Exempt from physical exertion and ensure quick-relief inhalers are accessible."
        )
    elif sensitive_students_count > 0:
        sensitive_students_notice = (
            f"All {sensitive_students_count} sensitive students can participate normally with standard observation."
        )
    else:
        sensitive_students_notice = "No sensitive students registered under special monitoring."

    # Best outdoor activity window
    best_window = find_best_outdoor_window(
        report.forecast,
        start_hour=policy.school_start_hour,
        end_hour=policy.school_end_hour,
    )

    # Status level and headline
    if cat == AQICategory.SEVERE or current_aqi >= 400:
        status_level = "HAZARDOUS"
        headline = "Keep PE & Assembly Indoors Today: Severe Air Quality"
    elif cat == AQICategory.VERY_POOR or current_aqi >= 301:
        status_level = "RESTRICTED"
        headline = "Keep PE Indoors & Mandate Masks: Very Poor Air Quality"
    elif cat == AQICategory.POOR or current_aqi >= 201 or forecast_spike:
        status_level = "RESTRICTED"
        headline = "Move High-Exertion Activities Indoors: Poor Air Quality"
    elif cat == AQICategory.MODERATE or current_aqi >= 101:
        status_level = "CAUTION"
        headline = "Moderate Air Quality: Outdoor Activities Permitted with Caution"
    else:
        status_level = "SAFE"
        headline = "Air Quality is Safe: Normal Outdoor Schedule"

    # Formulate 3 distinct numerical reasons
    reasons = [
        f"Current CPCB AQI is {current_aqi} ({cat.value}) with PM2.5 at {round(report.current.pm25, 1)} µg/m³.",
        f"Next 6-hour forecast peaks at AQI {peak_forecast_aqi} (PM2.5 {round(peak_forecast_pm25, 1)} µg/m³).",
    ]
    if sensitive_students_count > 0:
        reasons.append(f"{sensitive_students_count} sensitive students registered under respiratory protection protocol.")
    else:
        reasons.append(f"Dominant pollutant is {report.cpcb_current.dominant_pollutant.upper()} across nearby monitoring stations.")

    # High-clarity fallback messages
    principal_message_en = (
        f"ACTION REQUIRED ({headline.upper()}): "
        f"Current AQI is {current_aqi} ({cat.value}). "
        f"PE: {pe_action.replace('_', ' ').title()}. "
        f"Assembly: {assembly_action.replace('_', ' ').title()}. "
        f"Masks: {mask_advisory.replace('_', ' ').title()}. "
        f"Windows: {ventilation_advice.replace('_', ' ').title()}. "
        f"{sensitive_students_notice}"
    )

    if status_level in ("HAZARDOUS", "RESTRICTED"):
        parent_message_en = (
            f"Dear Parents, today's AQI is {current_aqi} ({cat.value}). "
            f"To protect student health, all PE and outdoor assemblies are moved indoors. "
            f"Classrooms will remain closed with air filtration. "
            f"Students are advised to wear masks during school transit."
        )
        parent_message_hi = (
            f"अभिभावक ध्यान दें: आज वायु गुणवत्ता सूचकांक (AQI) {current_aqi} ({cat.value}) है। "
            f"बच्चों की सुरक्षा हेतु आज शारीरिक शिक्षा (PE) और प्रार्थना सभा इनडोर होगी। "
            f"कक्षाओं में खिड़कियां बंद रहेंगी और एयर प्यूरीफायर चालू हैं। "
            f"आते-जाते समय बच्चों को मास्क पहनने की सलाह दी जाती है।"
        )
    elif status_level == "CAUTION":
        parent_message_en = (
            f"Dear Parents, today's AQI is {current_aqi} (Moderate). "
            f"Regular classes will proceed outdoors with reduced physical strain. "
            f"Sensitive students are being monitored."
        )
        parent_message_hi = (
            f"अभिभावक ध्यान दें: आज AQI {current_aqi} (मध्यम) है। "
            f"कक्षाएं और खेल सामान्य रूप से चलेंगे, लेकिन संवेदनशील बच्चों पर विशेष निगरानी रखी जा रही है।"
        )
    else:
        parent_message_en = (
            f"Dear Parents, today's air quality is {cat.value} (AQI {current_aqi}). "
            f"All outdoor sports and normal school activities will proceed as planned."
        )
        parent_message_hi = (
            f"अभिभावक ध्यान दें: आज वायु गुणवत्ता {cat.value} (AQI {current_aqi}) है। "
            f"सभी खेलकूद और बाहरी गतिविधियां सामान्य रूप से आयोजित की जाएंगी।"
        )

    return DecisionOutput(
        headline=headline,
        status_level=status_level,
        pe_action=pe_action,
        recess_action=recess_action,
        assembly_action=assembly_action,
        mask_advisory=mask_advisory,
        ventilation_advice=ventilation_advice,
        sensitive_students_notice=sensitive_students_notice,
        best_window=best_window,
        reasons=reasons,
        principal_message_en=principal_message_en,
        parent_message_en=parent_message_en,
        parent_message_hi=parent_message_hi,
        applied_policy=policy.to_dict(),
        current_aqi=current_aqi,
        current_category=cat.value,
        peak_forecast_aqi=peak_forecast_aqi,
    )
