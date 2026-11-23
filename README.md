# Scam-Message Triage Agent (Swarm + LlamaIndex)

A simple, real-time scam detection app built with a **4-agent Swarm handoff pattern** and **LlamaIndex** retrieval. Paste or forward any suspicious SMS, WhatsApp message, or call transcript to get the scam type, official advisory evidence, risk level, and one clear next step.

## Why This Project?

Digital-arrest and cyber-fraud scams rely on fear and urgency so victims pay before they can think or verify. Helplines like **1930** and RBI advisories already exist, but most people reach them after the money is already gone.

This app gives a **calm, evidence-backed second opinion** in seconds:
- **Swarm (Orchestration):** Splits the work across four small specialist agents using handoffs.
- **LlamaIndex (Grounding):** Searches official advisories so the answer is backed by real documents instead of guessing.

## How It Works (4-Agent Pipeline)

    Suspicious Message
           |
           v
    1. Classifier Agent   --> Identifies scam type (Digital-Arrest, KYC, OTP/UPI, Lottery/Job)
           | (Handoff)
           v
    2. Retrieval Agent    --> Queries LlamaIndex for the closest official advisory
           | (Handoff)
           v
    3. Risk Scorer Agent  --> Combines urgency cues + LlamaIndex similarity score
           | (Handoff)
           v
    4. Advisor Agent      --> Gives ONE clear next action (Ignore, Verify, or Dial 1930)

> **Note:** OpenAI deprecated the original Swarm library in March 2025 in favor of the Agents SDK. This project implements the exact same **handoff loop** in simple Python and uses local embeddings, so it runs **100% free with no API key**.

## Tech Stack

| Component | Role | Tool |
| :--- | :--- | :--- |
| **Orchestration** | 4-agent handoff loop | Core Python (Swarm pattern) |
| **Retrieval (RAG)** | Grounded document search | `llama-index-core` (`VectorStoreIndex`) |
| **Embeddings** | Local semantic matching | `sentence-transformers/all-MiniLM-L6-v2` |
| **Knowledge Base** | Official guidance | RBI & `cybercrime.gov.in` advisories |
| **Web Interface** | Chat-style demo UI | Streamlit (built using official Streamlit docs) |

## Project Files

    .
    ├── scam_triage_app.py   # 4-agent Swarm + LlamaIndex + Streamlit chat UI
    ├── requirements.txt     # Required Python libraries
    └── README.md            # Project overview and setup steps

## How to Run Locally

1. Install the required packages:

       pip install -r requirements.txt

2. Start the Streamlit app:

       streamlit run scam_triage_app.py

## Deploy on Streamlit Cloud

1. Upload `scam_triage_app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. Open [share.streamlit.io](https://share.streamlit.io) and connect your repository.
3. Set the main file path to `scam_triage_app.py` and click **Deploy** (no API keys needed).

## Quick Demo Test Cases

- **Digital-Arrest Call (High Risk):** *"You are under digital arrest by CBI. Your Aadhaar is linked to money laundering. Don't disconnect and transfer savings to RBI account immediately."*
- **Fake KYC SMS (High Risk):** *"URGENT: Your bank KYC is expired and account will be blocked within 2 hours. Click here to update PAN now."*
- **UPI / OTP Trap (High Risk):** *"Congratulations! You got Rs 5000 cashback. Scan QR code and enter your UPI PIN immediately to receive money."*
- **Normal Message (Low Risk):** *"Hey, reached hostel safely. Let's meet at the canteen around 7 PM for dinner."*

## Cyber Crime Help (India)

- **Helpline:** Dial **1930**
- **Portal:** [cybercrime.gov.in](https://cybercrime.gov.in)

---

**Author:** Unknow4384735

**Program:** M.Sc. Computer Science (Big Data Analytics), Central University of Rajasthan (CURAJ)
