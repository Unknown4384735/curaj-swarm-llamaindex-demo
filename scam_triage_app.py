import streamlit as st
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

st.set_page_config(page_title="Scam-Message Triage Bot", layout="centered")


# ==========================================
# PART 1: LLAMAINDEX (4 Simple Steps)
# ==========================================
@st.cache_resource
def setup_llamaindex():
    # Step 1: Turn off OpenAI LLM so LlamaIndex runs 100% free (no API key)
    Settings.llm = None

    # Step 2: Load a free model that turns text into numbers (embeddings)
    embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    Settings.embed_model = embed_model

    # Step 3: Put real advisories into LlamaIndex Documents
    docs = [
        Document(
            text="Police, CBI, or Courts NEVER do a digital arrest on video call. Do not transfer money to any RBI account.",
            metadata={"source": "cybercrime.gov.in & CBI Advisory"},
        ),
        Document(
            text="Banks never send urgent SMS links to update KYC or PAN within 2 hours to stop account blocking.",
            metadata={"source": "RBI KYC Fraud Advisory"},
        ),
        Document(
            text="Never share OTP, enter your UPI PIN, or scan a QR code to receive cashback or refunds.",
            metadata={"source": "RBI UPI Safety Guidelines"},
        ),
        Document(
            text="Promises of daily income for liking videos or paying a fee to claim a lottery prize are online scams.",
            metadata={"source": "Cyber Crime Job & Lottery Alert"},
        ),
    ]

    # Step 4: Build the Vector Index and create a Retriever (gets top 1 match)
    index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)
    retriever = index.as_retriever(similarity_top_k=1)
    return retriever


# ==========================================
# PART 2: 4 SPECIALIST AGENTS (Basic Python)
# ==========================================

# Agent 1: Finds scam type using simple if/elif checks
def classifier_agent(data):
    msg = data["message"].lower()

    if "digital arrest" in msg or "cbi" in msg or "police" in msg or "fir" in msg or "parcel" in msg or "aadhaar" in msg:
        data["scam_type"] = "Digital-Arrest Scam"
    elif "kyc" in msg or "account blocked" in msg or "pan" in msg:
        data["scam_type"] = "KYC / Bank Freeze Scam"
    elif "otp" in msg or "upi pin" in msg or "qr" in msg or "cashback" in msg:
        data["scam_type"] = "OTP / UPI Phishing"
    elif "lottery" in msg or "prize" in msg or "daily income" in msg:
        data["scam_type"] = "Lottery / Fake Job Scam"
    else:
        data["scam_type"] = "Unknown / Normal"

    data["steps"].append("1. Classifier Agent -> Found: " + data["scam_type"])
    return "retrieval"  # Handoff to Agent 2


# Agent 2: Asks LlamaIndex for the closest official advisory
def retrieval_agent(data, retriever):
    results = retriever.retrieve(data["message"])
    top_match = results[0]

    score = 0.0
    if top_match.score is not None:
        score = round(top_match.score, 2)

    data["advisory"] = top_match.text
    data["source"] = top_match.metadata["source"]
    data["score"] = score

    data["steps"].append("2. Retrieval Agent (LlamaIndex) -> Matched: " + data["source"] + " (Score: " + str(score) + ")")
    return "risk"  # Handoff to Agent 3


# Agent 3: Checks fear/urgency words + LlamaIndex score
def risk_scorer_agent(data):
    msg = data["message"].lower()
    fear_words = ["urgent", "immediately", "don't disconnect", "arrest", "transfer", "blocked", "2 hours", "pay now"]

    has_fear = False
    for word in fear_words:
        if word in msg:
            has_fear = True

    if data["scam_type"] != "Unknown / Normal" and (has_fear or data["score"] >= 0.45):
        data["risk"] = "HIGH RISK"
    elif data["scam_type"] != "Unknown / Normal" or has_fear:
        data["risk"] = "MEDIUM RISK"
    else:
        data["risk"] = "LOW RISK"

    data["steps"].append("3. Risk Scorer Agent -> Level: " + data["risk"])
    return "advisor"  # Handoff to Agent 4


# Agent 4: Writes one calm, clear next action
def advisor_agent(data):
    if data["risk"] == "HIGH RISK":
        data["advice"] = "HIGH RISK (" + data["scam_type"] + "): Hang up or block immediately. Do NOT pay or share OTP. Dial 1930 or visit cybercrime.gov.in."
    elif data["risk"] == "MEDIUM RISK":
        data["advice"] = "MEDIUM RISK: Message looks suspicious. Do not hurry—verify directly with your bank or family first."
    else:
        data["advice"] = "LOW RISK: No known scam pattern matched. Still, never share OTP or transfer money to strangers."

    data["steps"].append("4. Advisor Agent -> Final action ready.")
    return "done"  # Swarm finishes


# SWARM LOOP: Passes control from one agent to the next
def run_swarm(message, retriever):
    data = {"message": message, "steps": []}
    current_agent = "classifier"

    while current_agent != "done":
        if current_agent == "classifier":
            current_agent = classifier_agent(data)
        elif current_agent == "retrieval":
            current_agent = retrieval_agent(data, retriever)
        elif current_agent == "risk":
            current_agent = risk_scorer_agent(data)
        elif current_agent == "advisor":
            current_agent = advisor_agent(data)

    return data


# ==========================================
# PART 3: CHAT UI (From Streamlit Docs)
# ==========================================
st.title("Scam-Message Triage Bot")
st.caption("Swarm 4-Agent Handoff + LlamaIndex Advisory Search")

with st.spinner("Loading LlamaIndex..."):
    retriever = setup_llamaindex()

# Quick 1-click demo buttons
col1, col2, col3 = st.columns(3)
sample = ""

if col1.button("Digital Arrest"):
    sample = "You are under digital arrest by CBI. Don't disconnect and transfer money to RBI account immediately."
if col2.button("Fake KYC SMS"):
    sample = "URGENT: Your KYC is expired. Account will be blocked in 2 hours. Update PAN now."
if col3.button("Normal Message"):
    sample = "Hey, reached hostel safely. Let's meet at the canteen at 7 PM."

typed = st.chat_input("Paste a suspicious message here...")

if typed:
    message = typed
else:
    message = sample

if message == "":
    st.info("Click a demo button above or paste any message below.")
    st.stop()

# Run the 4-agent swarm
result = run_swarm(message, retriever)

# Show mobile-style chat bubbles
with st.chat_message("user"):
    st.write("Fwd: " + message)

with st.chat_message("assistant"):
    if result["risk"] == "HIGH RISK":
        st.error(result["advice"])
    elif result["risk"] == "MEDIUM RISK":
        st.warning(result["advice"])
    else:
        st.success(result["advice"])

    if result["risk"] != "LOW RISK":
        st.write("**Official Advisory (" + result["source"] + "):**")
        st.caption(result["advisory"])

# Show the 4 agent handoff steps
with st.expander("See 4-Agent Swarm Handoff Steps", expanded=True):
    for step in result["steps"]:
        st.write(step)
