"""Command-line interface (CLI) for Air Duty Officer.

Provides local execution, demo mode playback, live evaluation, and inspection.
Usage:
    python -m airduty.cli run --demo
    python -m airduty.cli run --live --lat 28.6139 --lon 77.2090
    python -m airduty.cli status
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

# Ensure UTF-8 output on Windows consoles for Hindi text and Unicode symbols
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from airduty.data import get_air_data, load_demo_fixture
from airduty.rules import SchoolPolicy, evaluate_school_safety

# ANSI terminal colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"


def get_color_for_category(category: str) -> str:
    cat = category.lower()
    if "good" in cat:
        return GREEN
    elif "satisfactory" in cat:
        return GREEN
    elif "moderate" in cat:
        return YELLOW
    elif "poor" in cat and "very" not in cat:
        return ORANGE
    elif "very poor" in cat:
        return RED
    elif "severe" in cat:
        return MAGENTA
    return RESET


def render_terminal_dashboard(
    school_name: str,
    lat: float,
    lon: float,
    sensitive_students: int,
    air_report,
    decision,
) -> None:
    cat_color = get_color_for_category(decision.current_category)

    print("\n" + "=" * 70)
    print(f"{BOLD}{CYAN}🏫 AIR DUTY OFFICER FOR SCHOOLS - MORNING DISPATCH{RESET}")
    print("=" * 70)
    print(f"School:       {BOLD}{school_name}{RESET} ({lat:.4f}, {lon:.4f})")
    print(f"Mode:         {BOLD}{'[DEMO FIXTURE - SEVERE EPISODE]' if air_report.is_demo else '[LIVE TELEMETRY]'}{RESET}")
    print(f"Sens. Pupils: {sensitive_students} students under respiratory tracking")
    print("-" * 70)

    # Current AQI Card
    print(f"{BOLD}CURRENT AIR QUALITY:{RESET}")
    print(
        f"  CPCB AQI:     {cat_color}{BOLD}{decision.current_aqi} ({decision.current_category.upper()}){RESET}"
    )
    print(f"  PM2.5:        {round(air_report.current.pm25, 1)} µg/m³")
    print(f"  PM10:         {round(air_report.current.pm10, 1)} µg/m³")
    print(f"  Telemetry:    {air_report.current.source}")

    if air_report.waqi_cross_check and air_report.waqi_cross_check.available:
        print(f"  Ground Cross: {air_report.waqi_cross_check.station_name} (AQI {air_report.waqi_cross_check.aqi})")

    print("-" * 70)
    # Decision Card
    print(f"{BOLD}OPERATIONAL DIRECTIVE:{RESET}")
    print(f"  {cat_color}{BOLD}► {decision.headline}{RESET}")
    print(f"  Status Level: {decision.status_level}")
    print(f"  Outdoor PE:   {decision.pe_action.replace('_', ' ').upper()}")
    print(f"  Assembly:     {decision.assembly_action.replace('_', ' ').upper()}")
    print(f"  Recess:       {decision.recess_action.replace('_', ' ').upper()}")
    print(f"  Masks:        {decision.mask_advisory.replace('_', ' ').upper()}")
    print(f"  Ventilation:  {decision.ventilation_advice.replace('_', ' ').upper()}")

    if decision.best_window:
        bw = decision.best_window
        print(f"  Best Window:  {BOLD}{bw.start_time.split('T')[1]} - {bw.end_time.split('T')[1]}{RESET} (Avg PM2.5: {bw.avg_pm25} µg/m³)")

    print("-" * 70)
    print(f"{BOLD}KEY REASONS:{RESET}")
    for idx, r in enumerate(decision.reasons, 1):
        print(f"  {idx}. {r}")

    print("-" * 70)
    print(f"{BOLD}BILINGUAL PARENT NOTIFICATION:{RESET}")
    print(f"{BOLD}[English]:{RESET}\n  \"{decision.parent_message_en}\"")
    print(f"{BOLD}[Hindi / हिन्दी]:{RESET}\n  \"{decision.parent_message_hi}\"")
    print("=" * 70 + "\n")


def execute_run(
    demo: bool = False,
    lat: float = 28.6139,
    lon: float = 77.2090,
    school_name: str = "Delhi Model School",
    sensitive_students: int = 45,
    output_json: bool = False,
) -> dict:
    if demo:
        air_report = load_demo_fixture()
    else:
        air_report = get_air_data(lat=lat, lon=lon, force_demo=False)

    policy = SchoolPolicy()
    decision = evaluate_school_safety(
        report=air_report,
        policy=policy,
        sensitive_students_count=sensitive_students,
    )

    result = {
        "school": {
            "name": school_name,
            "lat": lat,
            "lon": lon,
            "sensitive_students_count": sensitive_students,
        },
        "air_report": air_report.to_dict(),
        "decision": decision.to_dict(),
    }

    if output_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        render_terminal_dashboard(
            school_name=school_name,
            lat=lat,
            lon=lon,
            sensitive_students=sensitive_students,
            air_report=air_report,
            decision=decision,
        )

    return result


def main():
    parser = argparse.ArgumentParser(
        prog="airduty",
        description="Air Duty Officer for Schools - CLI Runner",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    run_parser = subparsers.add_parser("run", help="Run morning air quality evaluation")
    run_parser.add_argument("--demo", action="store_true", help="Replay recorded severe day fixture")
    run_parser.add_argument("--live", action="store_true", help="Fetch live telemetry from Open-Meteo")
    run_parser.add_argument("--lat", type=float, default=float(os.environ.get("DEFAULT_SCHOOL_LAT", 28.6139)), help="Latitude")
    run_parser.add_argument("--lon", type=float, default=float(os.environ.get("DEFAULT_SCHOOL_LON", 77.2090)), help="Longitude")
    run_parser.add_argument("--school-name", type=str, default=os.environ.get("DEFAULT_SCHOOL_NAME", "Delhi Model School"))
    run_parser.add_argument("--sensitive-students", type=int, default=int(os.environ.get("DEFAULT_SENSITIVE_STUDENTS", 45)))
    run_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        demo_mode = getattr(args, "demo", False)
        # Default to demo if neither --live nor --demo is specified or if requested
        if not getattr(args, "live", False) and not demo_mode:
            demo_mode = True

        execute_run(
            demo=demo_mode,
            lat=getattr(args, "lat", 28.6139),
            lon=getattr(args, "lon", 77.2090),
            school_name=getattr(args, "school_name", "Delhi Model School"),
            sensitive_students=getattr(args, "sensitive_students", 45),
            output_json=getattr(args, "json", False),
        )


if __name__ == "__main__":
    main()
