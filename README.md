# Air Duty Officer for Schools 🏫🍃

[![AWS Powered](https://img.shields.io/badge/AWS-Serverless-orange.svg)](https://aws.amazon.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hackathon](https://img.shields.io/badge/Hackathon-WeMakeDevs_x_AWS_Bharat_Builds-green.svg)](https://wemakedevs.org)

> An automated, agentic Air Quality Duty Officer designed for school principals and parents across India. Every morning at 06:00 IST, it reads live pollution telemetry and forecasts, applies safety policies, and delivers deterministic decisions with clear bilingual guidance (English + Hindi).

---

## 🚨 The Problem

On severe-air days across Indian metros, school principals face a daily dilemma: they have raw AQI numbers from news feeds or sensor apps, but **no operational clarity**.
- *Should morning assembly happen outdoors?*
- *Is recess safe for young children?*
- *What about the 45 students with asthma or respiratory sensitivities?*
- *What clear, reassuring message can be sent immediately to parents?*

Because raw data requires manual interpretation, protective actions are delayed, exposing vulnerable school children to toxic PM2.5 and PM10 spikes.

---

## 💡 The Solution

**Air Duty Officer for Schools** bridges the gap between environmental monitoring and daily school operations:
1. **Automated Morning Assessment**: An AWS EventBridge trigger fires daily at 06:00 IST (00:30 UTC).
2. **Multi-Source Telemetry**: Pulls hourly PM2.5 & PM10 data and 24-48h forecasts from Open-Meteo (with optional WAQI ground station cross-check).
3. **Official Indian CPCB Breakpoints**: In-code calculation of Indian Central Pollution Control Board (CPCB) sub-indices and categories (*Good, Satisfactory, Moderate, Poor, Very Poor, Severe*).
4. **Deterministic Rules Engine**: Maps AQI + peak forecast spikes + sensitive-student count to concrete school operations (PE, assembly, recess, ventilation, mask advisory, best outdoor activity window).
5. **Strands Agents SDK + Amazon Bedrock**: Generates structured, empathetic reasoning in English and Hindi for parents and administrators.
6. **Multi-Channel Alert Dispatch**: Dispatches immediate notifications through Amazon SNS (Email/SMS).
7. **Mobile-First Principal Dashboard**: High-contrast, single-page web app with real-time decisions, 24-hour PM2.5 forecast chart highlighting the cleanest window, and a one-click Demo Mode.

---

## 📐 Architecture & AWS Integration

- **Amazon Bedrock**: Powers natural language synthesis via the open-source AWS Strands Agents SDK.
- **AWS Lambda (Python 3.12)**: Serverless compute executing data ingestion, CPCB sub-index math, deterministic safety policy, and HTTP API handling.
- **Amazon EventBridge**: Triggers the morning evaluation schedule at 06:00 IST (`cron(30 0 ? * MON-FRI *)`).
- **Amazon DynamoDB**: Key-value persistence for `Schools` configuration and immutable `Decisions` audit history.
- **Amazon SNS**: Broadcasts instant action bulletins to subscribed principals and parents.
- **AWS SAM (Serverless Application Model)**: Complete Infrastructure as Code (IaC) for zero-friction deployment (`sam build && sam deploy --guided`).

---

## 🇮🇳 CPCB Breakpoint Verification

Air Duty Officer calculates the Indian National Air Quality Index (AQI) strictly following the Central Pollution Control Board (CPCB) National Air Quality Index Guidelines:

| Category | PM2.5 (24h avg, µg/m³) | PM10 (24h avg, µg/m³) | CPCB AQI Range |
| :--- | :--- | :--- | :--- |
| **Good** | 0 – 30 | 0 – 50 | 0 – 50 |
| **Satisfactory** | 31 – 60 | 51 – 100 | 51 – 100 |
| **Moderate** | 61 – 90 | 101 – 250 | 101 – 200 |
| **Poor** | 91 – 120 | 251 – 350 | 201 – 300 |
| **Very Poor** | 121 – 250 | 351 – 430 | 301 – 400 |
| **Severe** | 251+ | 430+ | 401 – 500+ |

*Verified against CPCB Ministry of Environment, Forest and Climate Change guidelines (2014-2015 NAQI).*

---

## 🛠️ Quickstart & Local Development

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12 / 3.14)
- AWS CLI & SAM CLI (for deployment)

### 2. Setup
```bash
git clone https://github.com/<your-username>/air-duty-officer.git
cd air-duty-officer
pip install -r backend/requirements.txt
cp .env.example .env
```

### 3. Run Offline Demo CLI
```bash
python -m airduty.cli run --demo
```

### 4. Run Live Telemetry CLI
```bash
python -m airduty.cli run --live
```

### 5. Launch Local Dev Server & Web UI
```bash
python -m airduty.handler
```
Open [http://localhost:8000/index.html](http://localhost:8000/index.html) in your browser.

### 6. Run Full Unit Test Suite (36 tests)
```bash
pytest backend/tests -v
```

---

## 📚 Documentation
- [System Architecture & Mermaid Diagrams](docs/architecture.md)
- [2:45 Video Demo Script](docs/demo-script.md)
- [Hackathon Submission Writeup](docs/writeup.md)
- [AI Tools Attribution](AI_TOOLS.md)

---

## 🚀 AWS Deployment with SAM

```bash
sam build
sam deploy --guided
```

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).

