import os
import streamlit as st
import requests

# Read backend URL from environment — set in Streamlit Cloud secrets
# Falls back to localhost for local development
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="CloudDash Support", layout="wide")

# ── session state ──
if "conversation_id" not in st.session_state or st.session_state.conversation_id is None:
    st.session_state.conversation_id = None
    st.session_state.trace_id = None
    st.session_state.messages = []
    st.session_state.health = None

def check_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        st.session_state.health = r.json() if r.status_code == 200 else None
    except:
        st.session_state.health = None

def start_conv():
    r = requests.post(f"{BACKEND_URL}/conversations", timeout=30)
    d = r.json()
    st.session_state.conversation_id = d["conversation_id"]
    st.session_state.trace_id = d["trace_id"]
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("CloudDash Support")
    if st.button("New Conversation"):
        start_conv()
        st.rerun()
        
    check_health()
    if st.session_state.health:
        st.success("Backend Online")
        with st.expander("System Status", expanded=True):
            st.json(st.session_state.health)
    else:
        st.error("Backend Offline")

# Chat UI
st.title("Support Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].replace("\n", "  \n"))
        if msg["role"] == "assistant":
            st.caption(f"Agent: **{msg.get('agent', 'unknown').upper()}**")
            citations = msg.get("citations", [])
            if citations:
                with st.expander("Citations"):
                    for c in citations:
                        st.write(f"- {c.get('title')} ({c.get('article_id')}) - Score: {c.get('score', 0):.2f}")

if prompt := st.chat_input("Describe your issue..."):
    if not st.session_state.conversation_id:
        start_conv()
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.spinner("Processing..."):
        try:
            r = requests.post(
                f"{BACKEND_URL}/conversations/{st.session_state.conversation_id}/messages",
                json={"message": prompt}, timeout=120)
            if r.status_code == 200:
                d = r.json()
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": d["response"]["content"],
                    "agent": d["response"]["agent"],
                    "citations": d["response"].get("citations", [])
                })
                st.rerun()
            else:
                st.error(f"Error: {r.text}")
        except Exception as e:
            st.error(f"Failed to connect: {e}")