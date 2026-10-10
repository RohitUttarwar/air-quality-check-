# AI Tools Used in Project Development

This project was conceived, planned, and built during the **Environmental Hacks (WeMakeDevs x AWS, Bharat Builds Tour - Air Track)**.

## Primary AI Assistants & SDKs

1. **Google Antigravity Agentic IDE**
   - **Role**: Primary autonomous pair programming agent and engineering workspace.
   - **Tasks**: Architecture design, CPCB AQI breakpoint calculation logic, deterministic policy rules engine, SAM template generation, unit testing, and full-stack integration.

2. **AWS Strands Agents SDK (`strands-agents`)**
   - **Role**: Open-source AWS agentic framework powering the intelligent air duty officer.
   - **Tasks**: Orchestrating agent tool calling (`get_air_quality`, `get_forecast`, `compute_cpcb_aqi`, `get_school_policy`, `draft_alert`), synthesis of live environmental telemetry, and multi-lingual natural language explanations.

3. **Amazon Bedrock (Claude 3 Haiku / Amazon Nova Micro)**
   - **Role**: Foundation LLM provider hosted on AWS infrastructure.
   - **Tasks**: Drafting structured, concise natural language reasoning in English and Hindi for school principals and parents without overriding deterministic safety boundaries.

4. **Deterministic Fallback Engine**
   - **Role**: Offline/failure-resilient safety generator designed to eliminate hallucination risk.
   - **Tasks**: Provides 100% deterministic template-based alerts if Bedrock is unreachable or rate-limited.
