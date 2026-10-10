// Static demo data so the dashboard works when no backend API is available (e.g. on Netlify).
// Generated from fixtures/severe_day.json via the backend rules engine.
window.OFFLINE_FIXTURE = {
  "school": {
    "school_id": "delhi-model-school-01",
    "name": "Delhi Model School",
    "lat": 28.6139,
    "lon": 77.209,
    "grade_range": "K-12",
    "sensitive_students_count": 45,
    "contact_emails": [
      "principal@school.edu"
    ],
    "contact_phones": [
      "+919876543210"
    ],
    "policy_thresholds": {
      "pe_indoor_threshold": 201,
      "recess_indoor_threshold": 201,
      "assembly_indoor_threshold": 150,
      "mask_recommended_threshold": 150,
      "mask_mandatory_threshold": 301,
      "sensitive_trigger_threshold": 101,
      "forecast_spike_buffer": 250,
      "school_start_hour": 7,
      "school_end_hour": 15
    }
  },
  "air_report": {
    "lat": 28.6139,
    "lon": 77.209,
    "current": {
      "timestamp": "2026-11-15T06:00",
      "pm25": 315.6,
      "pm10": 462.4,
      "source": "Open-Meteo Air Quality (Recorded Fixture)"
    },
    "cpcb_current": {
      "aqi": 451,
      "category": "Severe",
      "pm25_sub_index": 451,
      "pm10_sub_index": 447,
      "pm25_value": 315.6,
      "pm10_value": 462.4,
      "dominant_pollutant": "pm2_5",
      "color_hex": "#7E0023",
      "description": "Affects healthy people and seriously impacts those with existing diseases."
    },
    "forecast": [
      {
        "time": "2026-11-15T06:00",
        "pm25": 315.6,
        "pm10": 462.4,
        "cpcb_aqi": 451,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T07:00",
        "pm25": 330.2,
        "pm10": 480.1,
        "cpcb_aqi": 472,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T08:00",
        "pm25": 345.0,
        "pm10": 495.0,
        "cpcb_aqi": 493,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T09:00",
        "pm25": 320.4,
        "pm10": 470.2,
        "cpcb_aqi": 458,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T10:00",
        "pm25": 285.0,
        "pm10": 420.0,
        "cpcb_aqi": 428,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T11:00",
        "pm25": 255.0,
        "pm10": 390.5,
        "cpcb_aqi": 405,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T12:00",
        "pm25": 230.2,
        "pm10": 360.0,
        "cpcb_aqi": 385,
        "cpcb_category": "Very Poor",
        "color_hex": "#E53935"
      },
      {
        "time": "2026-11-15T13:00",
        "pm25": 210.5,
        "pm10": 340.0,
        "cpcb_aqi": 370,
        "cpcb_category": "Very Poor",
        "color_hex": "#E53935"
      },
      {
        "time": "2026-11-15T14:00",
        "pm25": 215.0,
        "pm10": 345.0,
        "cpcb_aqi": 373,
        "cpcb_category": "Very Poor",
        "color_hex": "#E53935"
      },
      {
        "time": "2026-11-15T15:00",
        "pm25": 235.4,
        "pm10": 365.2,
        "cpcb_aqi": 389,
        "cpcb_category": "Very Poor",
        "color_hex": "#E53935"
      },
      {
        "time": "2026-11-15T16:00",
        "pm25": 270.8,
        "pm10": 410.0,
        "cpcb_aqi": 417,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T17:00",
        "pm25": 305.0,
        "pm10": 450.0,
        "cpcb_aqi": 443,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T18:00",
        "pm25": 340.2,
        "pm10": 490.0,
        "cpcb_aqi": 486,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T19:00",
        "pm25": 365.0,
        "pm10": 515.0,
        "cpcb_aqi": 521,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T20:00",
        "pm25": 380.5,
        "pm10": 530.0,
        "cpcb_aqi": 542,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T21:00",
        "pm25": 370.0,
        "pm10": 520.0,
        "cpcb_aqi": 528,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T22:00",
        "pm25": 355.0,
        "pm10": 505.0,
        "cpcb_aqi": 507,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-15T23:00",
        "pm25": 340.0,
        "pm10": 490.0,
        "cpcb_aqi": 486,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-16T00:00",
        "pm25": 325.0,
        "pm10": 475.0,
        "cpcb_aqi": 465,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-16T01:00",
        "pm25": 315.0,
        "pm10": 460.0,
        "cpcb_aqi": 451,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-16T02:00",
        "pm25": 305.0,
        "pm10": 450.0,
        "cpcb_aqi": 443,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-16T03:00",
        "pm25": 298.0,
        "pm10": 440.0,
        "cpcb_aqi": 438,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-16T04:00",
        "pm25": 290.0,
        "pm10": 435.0,
        "cpcb_aqi": 431,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      },
      {
        "time": "2026-11-16T05:00",
        "pm25": 288.0,
        "pm10": 430.0,
        "cpcb_aqi": 430,
        "cpcb_category": "Severe",
        "color_hex": "#7E0023"
      }
    ],
    "waqi_cross_check": {
      "station_name": "Anand Vihar, Delhi - DPCC",
      "aqi": 448,
      "pm25": 320.0,
      "pm10": 475.0,
      "available": true
    },
    "is_demo": true,
    "retrieved_at": "2026-10-10T12:45:12.522697+00:00"
  },
  "decision": {
    "headline": "Keep PE & Assembly Indoors Today: Severe Air Quality",
    "status_level": "HAZARDOUS",
    "pe_action": "indoor_only",
    "recess_action": "indoor_only",
    "assembly_action": "indoor_only",
    "mask_advisory": "mandatory_all",
    "ventilation_advice": "air_purifiers_active",
    "sensitive_students_notice": "Active precaution for 45 students with known respiratory conditions. Exempt from physical exertion and ensure quick-relief inhalers are accessible.",
    "best_window": {
      "start_time": "2026-11-15T13:00",
      "end_time": "2026-11-15T14:00",
      "avg_pm25": 212.8,
      "reason": "Lowest PM2.5 period during school day (~212.8 µg/m³)"
    },
    "reasons": [
      "Current CPCB AQI is 451 (Severe) with PM2.5 at 315.6 µg/m³.",
      "Next 6-hour forecast peaks at AQI 493 (PM2.5 345.0 µg/m³).",
      "45 sensitive students registered under respiratory protection protocol."
    ],
    "principal_message_en": "ACTION REQUIRED (KEEP PE & ASSEMBLY INDOORS TODAY: SEVERE AIR QUALITY): Current AQI is 451 (Severe). PE: Indoor Only. Assembly: Indoor Only. Masks: Mandatory All. Windows: Air Purifiers Active. Active precaution for 45 students with known respiratory conditions. Exempt from physical exertion and ensure quick-relief inhalers are accessible.",
    "parent_message_en": "Dear Parents, today's AQI is 451 (Severe). To protect student health, all PE and outdoor assemblies are moved indoors. Classrooms will remain closed with air filtration. Students are advised to wear masks during school transit.",
    "parent_message_hi": "अभिभावक ध्यान दें: आज वायु गुणवत्ता सूचकांक (AQI) 451 (Severe) है। बच्चों की सुरक्षा हेतु आज शारीरिक शिक्षा (PE) और प्रार्थना सभा इनडोर होगी। कक्षाओं में खिड़कियां बंद रहेंगी और एयर प्यूरीफायर चालू हैं। आते-जाते समय बच्चों को मास्क पहनने की सलाह दी जाती है।",
    "applied_policy": {
      "pe_indoor_threshold": 201,
      "recess_indoor_threshold": 201,
      "assembly_indoor_threshold": 150,
      "mask_recommended_threshold": 150,
      "mask_mandatory_threshold": 301,
      "sensitive_trigger_threshold": 101,
      "forecast_spike_buffer": 250,
      "school_start_hour": 7,
      "school_end_hour": 15
    },
    "current_aqi": 451,
    "current_category": "Severe",
    "peak_forecast_aqi": 493
  },
  "history": [],
  "is_demo": true
};
