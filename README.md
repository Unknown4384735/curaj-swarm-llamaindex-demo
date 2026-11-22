
# Scam-Message Triage Agent (Swarm + LlamaIndex)

A lightweight, real-time scam detection and triage assistant built with a **4-agent Swarm handoff pattern** and **LlamaIndex** retrieval grounding. Paste or forward a suspicious SMS, WhatsApp message, or call transcript to get an instant scam classification, official advisory evidence, risk score, and one clear next action.

---

## Why This Project?

Cyber scams-especially **"digital arrest"** calls impersonating Police, CBI, or RBI officials-rely on fear and urgency to force victims into transferring money before they can verify the claim. While helplines (**1930**) and bank advisories exist, victims often reach them *after* the money is gone.

This project acts as a **calm, evidence-backed second opinion** in real time:
- **Swarm (Orchestration):** Decides *who acts* by splitting the task across four small, testable specialist agents.
- **LlamaIndex (Grounding):** Decides *what they know* by retrieving verified guidance from official advisories instead of letting a model guess.

---

## Architecture (4-Agent Swarm Pipeline)

```text
Suspicious Message
       │
       ▼
1. Classifier Agent   ──► Detects scam type (Digital-Arrest, KYC, OTP/UPI, Lottery/Job)
       │ (Handoff)
       ▼
2. Retrieval Agent    ──► Queries LlamaIndex VectorStoreIndex for matching official advisory
       │ (Handoff)
       ▼
3. Risk Scorer Agent  ──► Weighs urgency/fear language + LlamaIndex similarity score
       │ (Handoff)
       ▼
4. Advisor Agent      ──► Outputs ONE clear next action (Ignore, Verify, or Report to 1930)
