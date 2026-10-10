# Air Duty Officer for Schools: Project Writeup

**Hackathon**: Environmental Hacks (WeMakeDevs x AWS, Bharat Builds Tour)  
**Track**: Air Quality Track  
**Deliverable**: Working MVP, Public GitHub Repository, <3 Minute YouTube Demo

---

## 1. The Problem: The Morning Pollution Dilemma in Indian Schools

In dozens of Indian urban centers—including Delhi-NCR, Mumbai, Patna, and Kanpur—winter air quality routinely spikes into the **Severe (AQI 400–500+)** category due to thermal temperature inversions, vehicle emissions, and regional crop residue burning.

School children are physiologically the most vulnerable demographic: their respiratory systems breathe more air per kilogram of body weight, and outdoor exertion during sports or morning assembly causes deep alveolar deposition of toxic PM2.5 and PM10 particles.

Yet, school principals face a daily operational bottleneck:
1. **Raw Numbers, No Decisions**: Weather apps report numbers like "AQI 384" without telling an administrator whether to cancel PE, move assembly indoors, or require masks.
2. **Delayed Protective Actions**: By the time administration notices air quality degradation at 10:00 AM, children have already spent 45 minutes exercising outdoors.
3. **Anxious Parents & Communication Overhead**: Parents flood school administrative phones demanding updates. Teachers struggle to compose clear, reassuring announcements in both English and vernacular languages like Hindi.

---

## 2. The Solution: Air Duty Officer for Schools

**Air Duty Officer for Schools** is an automated, AI-assisted, and safety-deterministic cloud platform that serves as a dedicated morning health officer for educational institutions:
- **06:00 IST Automated Awakening**: Amazon EventBridge schedules an automated run every morning before buses start rolling.
- **Official CPCB Sub-Index Math**: Implements Central Pollution Control Board (CPCB) linear interpolation sub-indices for PM2.5 and PM10.
- **Two-Layer Hybrid Decision Architecture**:
  1. *Deterministic Safety Rules Engine*: Pure Python policy engine guaranteeing reproducible safety boundaries (PE indoor, recess sheltered, assembly indoor, mandatory masks, ventilation).
  2. *Strands Agents SDK + Amazon Bedrock Agent*: Open-source AWS agentic SDK orchestrating 5 tools (`get_air_quality`, `get_forecast`, `compute_cpcb_aqi`, `get_school_policy`, `draft_alert`) to generate empathetic, context-aware bilingual directives in English and Hindi.
- **Optimal Outdoor Window Discovery**: Algorithmic detection of the cleanest 2-hour window during school hours so necessary transitions occur at lowest exposure.
- **Multi-Channel Alert Broadcast**: Dispatches direct bulletins via Amazon SNS (Email/SMS).
- **Principal Web Dashboard**: Mobile-optimized, high-contrast, accessible interface with real-time telemetry, 24-hour canvas forecast curve, and one-click Demo Mode.

---

## 3. Where AWS Fits & Architecture

| AWS Service | Architecture Role & Value |
| :--- | :--- |
| **AWS Lambda (Python 3.12)** | Executes telemetry fetching, CPCB sub-index math, deterministic safety policy, agent tool orchestration, and HTTP API routing without server management. |
| **Amazon EventBridge** | Automated cron trigger scheduled for 06:00 IST (`cron(30 0 ? * MON-FRI *)`) to ensure decisions are dispatched before the school day begins. |
| **Amazon Bedrock** | Foundation model inference (Claude 3 Haiku / Amazon Nova Micro) for natural language reasoning, non-technical explanations, and nuanced Hindi translation. |
| **AWS Strands Agents SDK** | Open-source AWS agentic framework orchestrating multi-step tool execution and prompt chaining. |
| **Amazon DynamoDB** | Ultra-low latency persistence: `AirDuty_Schools` (profiles and thresholds) and `AirDuty_Decisions` (immutable audit log). |
| **Amazon SNS** | Push notification broadcast of morning directives to principals, teachers, and parent mailing lists. |
| **Amazon API Gateway (HTTP API v2)** | High-throughput serverless REST interface connecting the mobile dashboard to Lambda. |
| **AWS SAM (Serverless Application Model)** | Declarative Infrastructure as Code (IaC) enabling reproducible deployment with `sam build && sam deploy --guided`. |

---

## 4. AI Tools Used

| Tool | Usage & Contribution |
| :--- | :--- |
| **Google Antigravity Agentic IDE** | Primary engineering workspace and pair programmer for scaffolding, code generation, CPCB mathematical verification, testing, and SAM template generation. |
| **AWS Strands Agents SDK (`strands-agents`)** | Open-source AWS framework powering agent tool definition, context management, and Bedrock invocation. |
| **Amazon Bedrock (Claude 3 Haiku / Nova Micro)** | Foundation model provider generating bilingual reasoning and parent messages without compromising safety invariants. |

---

## 5. Safety & Reliability Guarantees

A fundamental design requirement for safety-critical civic infrastructure is **zero hallucination risk**:
1. **Strict Safety Invariant**: The LLM is never allowed to relax or override physical safety directives computed by the deterministic rules engine. The LLM only explains and drafts.
2. **Deterministic Fallback**: If Bedrock is unreachable or credentials are absent, the system instantly falls back to pre-compiled templates in English and Hindi.
3. **Demo Mode Integrity**: Clear visual distinction between live telemetry and recorded severe pollution fixtures.
