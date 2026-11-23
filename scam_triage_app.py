import streamlit as st
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

st.set_page_config(page_title="Scam-Message Triage Bot", layout="wide")


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

    if "digital arrest" in msg or "cbi" in msg or "police" in msg or "fir" in msg or "parcel" in msg or "aadhaar"
