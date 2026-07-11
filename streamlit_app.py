"""DTDL Customer Intelligence Platform - Standalone Streamlit App."""
import streamlit as st
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="DTDL Customer Intelligence Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #E20074; text-align: center; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; text-align: center; margin-bottom: 2rem; }
    .stButton>button { background-color: #E20074; color: white; border-radius: 10px; font-weight: 600; }
    .stButton>button:hover { background-color: #C10064; }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "tickets_db" not in st.session_state:
    st.session_state.tickets_db = []
if "orchestrator" not in st.session_state:
    try:
        from orchestrator import AgentOrchestrator
        st.session_state.orchestrator = AgentOrchestrator()
        st.session_state.api_ready = True
    except Exception as e:
        st.session_state.orchestrator = None
        st.session_state.api_ready = False
        st.session_state.api_error = str(e)

with st.sidebar:
    st.title("DTDL")
    st.markdown("Customer Intelligence Platform")
    page = st.radio("", ["🏠 Dashboard", "💬 Live Chat", "📋 Tickets", "📊 Analytics", "🤖 Agents", "⚙️ System"])
    if st.session_state.api_ready:
        st.success("✅ AI Engine Ready")
    else:
        st.error("❌ AI Engine Error")

if page == "🏠 Dashboard":
    st.markdown('<div class="main-header">🤖 DTDL Customer Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Multi-Agent Customer Support</div>', unsafe_allow_html=True)
    
    tickets = st.session_state.tickets_db
    total = len(tickets)
    resolved = len([t for t in tickets if t.get("status") == "resolved"])
    escalated = len([t for t in tickets if t.get("status") == "escalated"])
    open_tickets = len([t for t in tickets if t.get("status") == "open"])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets", total)
    c2.metric("Resolution Rate", f"{resolved/total*100:.0f}%" if total else "0%")
    c3.metric("Escalated", escalated)
    c4.metric("Open", open_tickets)
    
    if tickets:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Intent Distribution")
            intents = {}
            for t in tickets:
                intents[t.get("intent", "general")] = intents.get(t.get("intent", "general"), 0) + 1
            fig = px.pie(values=list(intents.values()), names=list(intents.keys()), hole=0.5)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Priority Distribution")
            priorities = {}
            for t in tickets:
                priorities[t.get("priority", "medium")] = priorities.get(t.get("priority", "medium"), 0) + 1
            fig = px.bar(x=list(priorities.keys()), y=list(priorities.values()))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start chatting to see analytics!")

elif page == "💬 Live Chat":
    st.markdown('<div class="main-header">💬 Live Customer Support</div>', unsafe_allow_html=True)
    
    with st.expander("Customer Info"):
        c1, c2, c3 = st.columns(3)
        customer_name = c1.text_input("Name", value="John Doe")
        customer_phone = c2.text_input("Phone", value="+91-98765-43210")
        customer_id = c3.text_input("Customer ID")
    
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.info(f"👤 **{chat.get('customer_name', 'Customer')}**: {chat['message']}")
        else:
            st.success(f"🤖 **DTDL AI**: {chat['message']}")
            with st.expander("Details"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Intent", chat.get("intent", "N/A"))
                c2.metric("Confidence", f"{chat.get('confidence', 0):.0%}")
                c3.metric("Sentiment", f"{chat.get('sentiment', 0):.2f}")
                c4.metric("Time", f"{chat.get('processing_time', 0)}s")
                if chat.get("ticket_id"):
                    st.code(f"Ticket: {chat['ticket_id']}")
    
    message = st.text_area("Type message...", height=80, placeholder="Describe your issue...")
    
    c1, c2 = st.columns([1, 5])
    send = c1.button("Send", use_container_width=True)
    
    quick = st.columns(4)
    tests = [
        ("💰 Billing", "My bill is higher than usual. Can you explain the charges?"),
        ("📡 Technical", "I have no network signal since morning. Please help!"),
        ("😠 Retention", "I want to port out to Jio. Your service is terrible!"),
        ("🆘 Escalation", "I want to speak to a manager. This is fraud!")
    ]
    for i, (label, test_msg) in enumerate(tests):
        if quick[i].button(label, use_container_width=True, key=f"qt_{i}"):
            message = test_msg
            send = True
    
    if send and message and st.session_state.orchestrator:
        st.session_state.chat_history.append({"role": "user", "message": message, "customer_name": customer_name})
        
        with st.spinner("🤖 AI Agents processing..."):
            try:
                result = st.session_state.orchestrator.process_message(
                    message=message,
                    customer_context={"customer_name": customer_name, "customer_phone": customer_phone, "customer_id": customer_id}
                )
                st.session_state.tickets_db.append(result)
                st.session_state.chat_history.append({"role": "bot", "message": result.get("response", ""), **result})
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.rerun()
    elif send and message and not st.session_state.orchestrator:
        st.error("AI Engine not initialized. Check NVIDIA_API_KEY in secrets.")
    
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.tickets_db = []
        st.rerun()

elif page == "📋 Tickets":
    st.markdown('<div class="main-header">📋 Ticket Management</div>', unsafe_allow_html=True)
    tickets = st.session_state.tickets_db
    if tickets:
        df = pd.DataFrame([{
            "ticket_id": t.get("ticket_id"),
            "customer_id": t.get("customer_id"),
            "intent": t.get("intent"),
            "status": t.get("status"),
            "priority": t.get("priority"),
            "sentiment": t.get("sentiment"),
            "processing_time": t.get("processing_time")
        } for t in tickets])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No tickets yet. Start chatting!")

elif page == "📊 Analytics":
    st.markdown('<div class="main-header">📊 Analytics</div>', unsafe_allow_html=True)
    if st.session_state.orchestrator:
        stats = st.session_state.orchestrator.get_system_stats()
        if stats and stats.get("agents"):
            agent_data = []
            for name, metrics in stats["agents"].items():
                agent_data.append({
                    "Agent": metrics["agent_name"],
                    "Handled": metrics["tickets_handled"],
                    "Resolved": metrics["tickets_resolved"],
                    "Escalated": metrics["tickets_escalated"],
                    "Avg Response (s)": round(metrics["avg_response_time"], 2)
                })
            df = pd.DataFrame(agent_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Handled", x=df["Agent"], y=df["Handled"]))
            fig.add_trace(go.Bar(name="Resolved", x=df["Agent"], y=df["Resolved"]))
            fig.add_trace(go.Bar(name="Escalated", x=df["Agent"], y=df["Escalated"]))
            fig.update_layout(barmode="group", height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("AI Engine not ready")

elif page == "🤖 Agents":
    st.markdown('<div class="main-header">🤖 Agent Swarm</div>', unsafe_allow_html=True)
    if st.session_state.orchestrator:
        stats = st.session_state.orchestrator.get_system_stats()
        if stats and stats.get("agents"):
            for name, metrics in stats["agents"].items():
                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
                c1.write(f"**{metrics['agent_name']}**")
                c2.write(f"Handled: {metrics['tickets_handled']}")
                c3.write(f"Resolved: {metrics['tickets_resolved']}")
                c4.write(f"Escalated: {metrics['tickets_escalated']}")
                c5.write(f"Avg: {metrics['avg_response_time']:.2f}s")
                st.markdown("---")
    else:
        st.info("Agents not initialized")

elif page == "⚙️ System":
    st.markdown('<div class="main-header">⚙️ System Status</div>', unsafe_allow_html=True)
    st.subheader("Environment")
    st.write(f"NVIDIA_API_KEY: {'✅ Set' if os.environ.get('NVIDIA_API_KEY') else '❌ Not Set'}")
    st.subheader("Orchestrator Status")
    if st.session_state.orchestrator:
        st.success("✅ Orchestrator initialized")
    else:
        st.error(f"❌ Failed: {st.session_state.get('api_error', 'Unknown error')}")
    if st.button("Refresh"):
        st.rerun()
