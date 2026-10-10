# Air Duty Officer for Schools: 2:45 Demo Video Script

**Target Duration**: 2 minutes 45 seconds  
**Track**: Environmental Hacks (WeMakeDevs x AWS Bharat Builds Tour - Air Track)  
**Presenter**: Solo or Pair Team Member

---

## ⏱️ Video Breakdown

| Timestamp | Section | Visual on Screen | Spoken Script / Narration |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:30** | **The Problem** | Headline news of Delhi/North India winter smog; confused parent WhatsApp group mockup | *"Every winter morning across Indian schools, principals wake up to a raw AQI number—420, 480—and an impossible dilemma. Should kids do outdoor PE? Should assembly be cancelled? What about the 45 students with asthma? Principals aren't environmental scientists, and parents are anxious. Raw data without clear decisions puts children's lungs at risk."* |
| **0:30 – 1:00** | **Built on AWS** | **AWS Console live view**: <br/>1. EventBridge Schedule `06:00 IST` <br/>2. Lambda `AirDutyFunction`<br/>3. DynamoDB Tables `Schools` & `Decisions`<br/>4. SNS Topic `AirDuty_Alerts` | *"Introducing Air Duty Officer for Schools, built entirely on AWS serverless. Every morning at 06:00 IST sharp, an Amazon EventBridge rule triggers our AWS Lambda. Lambda fetches hourly PM2.5 data, calculates the official Indian CPCB AQI, and uses Amazon Bedrock with the open-source AWS Strands Agents SDK to synthesize a safe, deterministic operational directive stored in DynamoDB and dispatched through SNS."* |
| **1:00 – 1:45** | **The Web Dashboard (Mobile View)** | **Mobile browser view (390px width)** of `http://localhost:8000`: <br/>- Hero status card (Red glow)<br/>- 5 action badges (PE, Assembly, Recess, Masks, Purifiers)<br/>- 3 reasons with numbers<br/>- 24h PM2.5 chart with golden highlight | *"Here is the principal's mobile dashboard. Notice the design: big, high-contrast type that works on any phone. At one glance, the principal sees today's single decision: 'Keep PE & Assembly Indoors Today: Severe Air Quality'. Below are five operational directives: Outdoor PE is Indoor Only, Assembly is Indoors, Masks are Mandatory. Then, 3 clear numerical reasons. Look at our 24-hour forecast chart: our algorithm identifies the cleanest 2-hour window of the day—13:00 to 14:00—so if children must go outside for buses, they do so when PM2.5 dips 38%."* |
| **1:45 – 2:15** | **Demo Mode & Bilingual Hindi Message** | 1. Toggle "Demo Mode" switch<br/>2. Click "Run Now" (toast fires)<br/>3. Click "हिन्दी (Hindi)" button<br/>4. Click "Copy Message" | *"Judging conditions can be unpredictable, so we built a one-click Demo Mode replaying recorded severe winter telemetry. When we click 'Run Now', the agent evaluates live and broadcasts alerts. Parents don't want technical jargon—they need clear guidance. With one click, principals toggle to Hindi. 'अभिभावक ध्यान दें: आज AQI 451 है... शारीरिक शिक्षा इनडोर होगी।' Principals can copy and paste this directly into school WhatsApp broadcasts in two seconds."* |
| **2:15 – 2:45** | **Impact & Conclusion** | AWS Console showing SNS message delivery and DynamoDB audit record; school children smiling outdoors | *"Our safety invariant ensures zero AI hallucinations: Bedrock drafts empathetic explanations, but our deterministic rules engine strictly enforces safety thresholds. By deploying on AWS Serverless, Air Duty Officer costs pennies per month and can protect millions of school children across every district in Bharat. Thank you!"* |

---

## 🎬 Recording Checklist & Pro Tips
1. **Screen Setup**: Set browser window to mobile emulator (iPhone 14 / Pixel 7 view: 390x844px) during the Web UI segment (1:00 - 2:15) to demonstrate mobile-first design.
2. **AWS Console Tab**: Have AWS Console open with tabs for:
   - AWS Lambda Console (`AirDutyFunction`)
   - Amazon EventBridge Rules (`AirDuty_MorningEvaluation_0600IST`)
   - Amazon DynamoDB Tables (`AirDuty_Schools`, `AirDuty_Decisions`)
   - Amazon SNS (`AirDuty_Alerts`)
3. **Pacing**: Speak at a brisk, energetic tempo (approx. 140 words/minute).
4. **Resolution**: Record in 1080p 60fps with clear microphone audio.
