import streamlit as st
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

st.set_page_config(page_title="Scam-Message Triage Agent", layout="wide")


# ==========================================================
# 1. LLAMAINDEX KNOWLEDGE BASE (Official Advisories & Patterns)
# ==========================================================
ADVISORY_DOCS = [
    {
        "source": "cybercrime.gov.in & CBI Operation Chakra-VI Advisory",
        "type": "Digital-Arrest Scam",
        "text": (
            "Indian Police, CBI, ED, Customs, or Courts NEVER conduct a 'digital arrest' "
            "over video call or phone. Scammers falsely claim your Aadhaar, SIM, or courier parcel "
            "is linked to money laundering or drugs, threaten immediate arrest if you disconnect, "
            "and demand transferring savings to an 'RBI-monitored verification account'."
        ),
    },
    {
        "source": "RBI Kehta Hai — KYC & Account Block Advisory",
        "type": "KYC / Bank Freeze Scam",
        "text": (
            "Banks and RBI never send SMS links asking you to urgently update KYC, PAN, or "
            "net-banking credentials within 2 hours to prevent account freezing or suspension. "
            "Always verify directly through your official bank app or home branch."
        ),
    },
    {
        "source": "RBI Digital Payment Safety Guidelines",
        "type": "OTP / UPI Phishing",
        "text": (
            "Never share an OTP, CVV, PIN, or enter your UPI PIN to receive money or cashback. "
            "Entering a UPI PIN or scanning a QR code always deducts money from your account, "
            "never credits it."
        ),
    },
    {
        "source": "National Cyber Crime Portal — Job & Lottery Fraud Alert",
        "type": "Lottery / Fake Job Scam",
        "text": (
            "Messages promising guaranteed daily income for liking YouTube videos, prepaid task "
            "commissions, or unexpected lottery/prize winnings requiring a registration or "
            "processing fee are classic advance-fee cyber frauds."
        ),
    },
]


@st.cache_resource
def build_llamaindex_retriever():
    # Disable default OpenAI LLM so LlamaIndex runs 100% free & offline
    Settings.llm = None
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    Settings.embed_model = embed_model

    # Convert advisories into LlamaIndex Document objects
    docs = []
    for item in ADVISORY_DOCS:
        docs.append(
            Document(
                text=item["text"],
                metadata={"source": item["source"], "type": item["type"]},
            )
        )

    # Build LlamaIndex VectorStoreIndex and return Top-1 retriever
    index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)
    return index.as_retriever(similarity_top_k=1)


# ==========================================================
# 2. SWARM OF 4 SPECIALIST AGENTS (Explicit Handoff Pattern)
# ==========================================================

# AGENT 1: Classifier Agent -> identifies scam category & hands off to Retrieval Agent
def classifier_agent(state, retriever):
    msg = state["message"].lower()

    patterns = {
        "Digital-Arrest Scam": ["digital arrest", "cbi", "police", "fir", "parcel", "aadhaar", "money laundering", "rbi account", "video call", "don't disconnect"],
        "KYC / Bank Freeze Scam": ["kyc", "account blocked", "account suspended", "pan update", "bank account", "deactivated"],
        "OTP / UPI Phishing": ["otp", "upi pin", "cvv", "scan qr", "cashback", "refund link", "collect request"],
        "Lottery / Fake Job Scam": ["lottery", "won prize", "part-time job", "daily income", "processing fee", "telegram task"],
    }

    best_type = "No Known Scam Pattern"
    best_hits = 0

    for scam_type, keywords in patterns.items():
        hits = 0
        for word in keywords:
            if word in msg:
                hits += 1
        if hits > best_hits:
            best_hits = hits
            best_type = scam_type

    state["scam_type"] = best_type
    state["keyword_hits"] = best_hits
    state["trace"].append(
        f"**1. Classifier Agent:** Detected `{best_type}` ({best_hits} signal match(es)) → **Handoff to Retrieval Agent**"
    )
    return retrieval_agent


# AGENT 2: Retrieval Agent -> queries LlamaIndex for matching official advisory
def retrieval_agent(state, retriever):
    query = f"{state['scam_type']}: {state['message']}"
    results = retriever.retrieve(query)

    top_node = results[0]
    state["advisory_source"] = top_node.metadata["source"]
    state["advisory_text"] = top_node.text
    state["similarity_score"] = float(top_node.score or 0.0)

    state["trace"].append(
        f"**2. Retrieval Agent (LlamaIndex):** Grounded against `{state['advisory_source']}` "
        f"(similarity `{state['similarity_score']:.2f}`) → **Handoff to Risk Scorer**"
    )
    return risk_scorer_agent


# AGENT 3: Risk Scorer Agent -> weighs LlamaIndex match + urgency/fear language
def risk_scorer_agent(state, retriever):
    msg = state["message"].lower()
    urgency_words = [
        "urgent", "immediately", "don't disconnect", "within 1 hour", "within 2 hours",
        "arrest", "transfer", "blocked", "suspended", "pay now", "fine", "secret", "stay on call"
    ]

    found_urgency = []
    for word in urgency_words:
        if word in msg:
            found_urgency.append(word)

    sim = state["similarity_score"]
    hits = state["keyword_hits"]

    if hits >= 1 and (len(found_urgency) >= 1 or sim >= 0.45):
        risk = "HIGH RISK"
    elif hits >= 1 or (len(found_urgency) >= 1 and sim >= 0.40):
        risk = "MEDIUM RISK"
    else:
        risk = "LOW RISK"

    state["risk_level"] = risk
    state["urgency_flags"] = found_urgency
    state["trace"].append(
        f"**3. Risk Scorer Agent:** Urgency cues `{found_urgency or 'None'}` + LlamaIndex score `{sim:.2f}` "
        f"= **{risk}** → **Handoff to Advisor Agent**"
    )
    return advisor_agent


# AGENT 4: Advisor Agent -> writes ONE calm, evidence-backed next action
def advisor_agent(state, retriever):
    risk = state["risk_level"]
    scam = state["scam_type"]

    if risk == "HIGH RISK":
        if scam == "Digital-Arrest Scam":
            action = (
                "High risk — likely a **Digital-Arrest Scam**. **Hang up immediately**, "
                "do **NOT** transfer any money, and report it: **dial 1930** or visit **cybercrime.gov.in**."
            )
        else:
            action = (
                f"High risk — likely a **{scam}**. **Do not click links, share OTPs, or pay.** "
                "Block the sender and report at **1930** or **cybercrime.gov.in**."
            )
    elif risk == "MEDIUM RISK":
        action = (
            "Medium risk — suspicious urgency or pattern detected. **Do not act in a hurry.** "
            "Verify independently through an official phone number or bank branch before replying."
        )
    else:
        action = (
            "Low risk — no known scam pattern matched. Still, remember the golden rule: "
            "**never share OTPs or move money to unverified accounts.**"
        )

    state["final_advice"] = action
    state["trace"].append("**4. Advisor Agent:** Final grounded action generated → **Complete**")
    return None  # Swarm finishes


# SWARM ORCHESTRATOR LOOP (Same handoff mechanic taught by OpenAI Swarm)
def run_swarm(user_message, retriever):
    state = {"message": user_message, "trace": []}
    current_agent = classifier_agent

    while current_agent is not None:
        current_agent = current_agent(state, retriever)

    return state


# ==========================================================
# 3. MOBILE-FIRST CHAT UI (Streamlit Live Walkthrough)
# ==========================================================
st.title("Scam-Message Triage Bot")
st.caption("Swarm 4-Agent Handoff Pattern + LlamaIndex Grounding (RBI & cybercrime.gov.in Advisories)")

with st.spinner("Loading LlamaIndex knowledge base..."):
    retriever = build_llamaindex_retriever()

# Quick 1-click demo buttons so live demo never slows down
st.markdown("**Quick Demo Messages (Click to test):**")
c1, c2, c3, c4 = st.columns(4)
sample = ""

if c1.button("Digital-Arrest Call"):
    sample = "You are under digital arrest by CBI. Your Aadhaar is linked to money laundering. Don't disconnect and transfer savings to RBI account immediately."
if c2.button("Fake KYC SMS"):
    sample = "URGENT: Your bank KYC is expired and account will be blocked within 2 hours. Click here to update PAN now."
if c3.button("UPI / OTP Trap"):
    sample = "Congratulations! You got Rs 5000 cashback. Scan QR code and enter your UPI PIN immediately to receive money."
if c4.button("Normal Message"):
    sample = "Hey, reached hostel safely. Let's meet at the canteen around 7 PM for dinner."

user_input = st.chat_input("Paste or forward a suspicious message here...")
message = user_input or sample

if not message:
    st.info("Click a sample button above or paste any suspicious message in the chat box below.")
    st.stop()

# Run the 4-Agent Swarm
result = run_swarm(message, retriever)

# Show Chat Conversation (Matches Slide 10 Mobile Mockup)
with st.chat_message("user"):
    st.write(f"**Fwd:** {message}")

with st.chat_message("assistant"):
    if result["risk_level"] == "HIGH RISK":
        st.error(result["final_advice"])
    elif result["risk_level"] == "MEDIUM RISK":
        st.warning(result["final_advice"])
    else:
        st.success(result["final_advice"])

    if result["risk_level"] != "LOW RISK":
        st.markdown(f"**Grounded Evidence (`{result['advisory_source']}`):**")
        st.caption(result["advisory_text"])

# Under-the-Hood Handoff Trace (Matches Slide 9 Architecture)
with st.expander("Under the Hood: 4-Agent Swarm Handoff Trace", expanded=True):
    for step in result["trace"]:
        st.write(step)
