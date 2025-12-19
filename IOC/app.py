import streamlit as st
import os
import json
import time
from datetime import datetime
import pandas as pd
from agent import ClinicalAgent
import database
import utils

# --- Page Configuration ---
st.set_page_config(
    page_title="Clinical Orchestrator",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Realistic Look ---
st.markdown("""
<style>
    :root {
        --brand: #2e86de;
        --brand-2: #6c5ce7;
        --accent: #22c55e;
        --card-bg: #ffffff;
        --card-bg-soft: #f7fbff;
        --text: #1f2937;
        --muted: #64748b;
    }
    .main { background: linear-gradient(180deg, #0f172a 0%, #111827 40%, #0f172a 100%); }
    .stChatInput {
        border-radius: 10px;
    }
    .patient-card {
        background: linear-gradient(135deg, var(--card-bg) 0%, var(--card-bg-soft) 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(46,134,222,0.12);
        margin-bottom: 20px;
        border-left: 6px solid var(--brand);
    }
    .metric-card {
        background: linear-gradient(180deg, var(--card-bg) 0%, #f8fafc 100%);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #eef2f7;
        box-shadow: 0 6px 12px rgba(108,92,231,0.10);
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px) scale(1.01);
        border-color: rgba(46,134,222,0.4);
    }
    .audit-entry {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.75em;
        padding: 8px;
        border-bottom: 1px solid #f0f0f0;
        background-color: #fafafa;
        margin-bottom: 2px;
        border-radius: 4px;
    }
    .timeline-item {
        border-left: 2px solid #ddd;
        padding-left: 15px;
        margin-left: 5px;
        margin-bottom: 15px;
        position: relative;
    }
    .timeline-item::before {
        content: '';
        width: 10px;
        height: 10px;
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
        border-radius: 50%;
        position: absolute;
        left: -6px;
        top: 0;
    }
    .note-card {
        background: linear-gradient(180deg, #fff7d6 0%, #fff3cd 100%);
        border-left: 4px solid #ffb703;
        padding: 10px;
        margin-bottom: 10px;
        font-size: 0.9em;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(46,134,222,0.12);
        border: 1px solid rgba(46,134,222,0.35);
        color: #1e3a8a;
        font-weight: 600;
        font-size: 0.80em;
        margin-right: 8px;
    }
    .card-divider {
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, var(--brand) 0%, var(--brand-2) 100%);
        border-radius: 3px;
        margin: 8px 0 12px 0;
    }
    .patient-card p { color: var(--text); }
    .patient-card b { color: var(--text); }
    .note-card b { color: #8b5d00; }
    .note-card i { color: #4b5563; }
    .patient-card h4 { 
        color: #eaf2ff; 
        background: linear-gradient(90deg, var(--brand) 0%, var(--brand-2) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton>button, .st-emotion-cache-1emrehy { 
        background: linear-gradient(90deg, var(--brand) 0%, var(--brand-2) 100%) !important; 
        color: white !important; 
        border: none !important; 
        box-shadow: 0 8px 16px rgba(46,134,222,0.25) !important; 
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Settings & System Status ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/medical-doctor.png", width=64)
    st.title("System Control")
    
    with st.expander("⚙️ Configuration", expanded=True):
        api_key = st.text_input("HF API Key", type="password", value=os.environ.get("HF_API_KEY", "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"))
        model = st.selectbox(
            "LLM Model",
            ["Qwen/Qwen2.5-72B-Instruct", "meta-llama/Meta-Llama-3-70B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
        )
        dry_run = st.toggle("Dry Run Mode", value=False, help="Simulate actions without committing DB changes.")
    
    st.divider()
    
    st.subheader("🏥 Live System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div class='metric-card'><b>Patients</b><br>{len(database.PATIENTS)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card' style='margin-top:5px'><b>Docs</b><br>{len(database.DOCTORS)}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><b>Appts</b><br>{len(database.APPOINTMENTS)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-card' style='margin-top:5px'><b>Policies</b><br>{len(database.INSURANCE_POLICIES)}</div>", unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️ Reset Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent = None
        st.rerun()

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = ClinicalAgent(api_key=api_key, model=model, dry_run=dry_run)
else:
    # Update dynamic settings
    st.session_state.agent.dry_run = dry_run
    st.session_state.agent.model = model
    st.session_state.agent.client.api_key = api_key

# --- Main Layout ---
col_chat, col_context = st.columns([2, 1])

# === RIGHT COLUMN: Context & Audit ===
with col_context:
    st.subheader("📋 Clinical Context")
    
    # 1. Active Patient View (Mock logic: find last patient mentioned in tool calls)
    active_patient = None
    last_tool_result = None
    
    # Scan history for patient data
    for msg in reversed(st.session_state.messages):
        if "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                if tc["tool"] == "search_patient":
                    try:
                        res = json.loads(tc["result"])
                        if isinstance(res, list) and len(res) > 0:
                            active_patient = res[0]
                            break
                    except: pass
        if active_patient: break
    
    if active_patient:
        name_entry = active_patient.get("name", [{}])[0]
        full_name = f"{name_entry.get('given', [''])[0]} {name_entry.get('family', '')}"
        
        st.markdown(f"""
        <div class="patient-card">
            <h4>👤 {full_name}</h4>
            <div class="card-divider"></div>
            <p><b>ID:</b> {active_patient.get('id')}<br>
            <b>DOB:</b> {active_patient.get('dob')}<br>
            <span class="badge">{active_patient.get('gender').title()}</span>
            <span class="badge">📞 {active_patient.get('telecom', [{}])[0].get('value', 'N/A')}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Clinical Notes
        with st.expander("📝 Clinical Notes", expanded=True):
            notes = active_patient.get("clinical_notes", [])
            if notes:
                for note in notes:
                    st.markdown(f"""
                    <div class="note-card">
                        <b>{note['date']}</b> - {note['author']}<br>
                        <i>"{note['note']}"</i>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No clinical notes available.")

        # Patient History Timeline
        with st.expander("⏳ Patient History", expanded=False):
            history = active_patient.get("past_appointments", [])
            if history:
                for event in history:
                    st.markdown(f"""
                    <div class="timeline-item">
                        <b>{event['date']}</b><br>
                        {event['department']} - <span style="color:green">{event['status']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No history available.")

        # Raw FHIR View
        with st.expander("🔍 Raw FHIR Resource", expanded=False):
            st.json(active_patient)
    else:
        st.info("No active patient context detected.")

    # 2. Upcoming Appointments (from DB)
    st.subheader("📅 Recent Bookings")
    if database.APPOINTMENTS:
        df = pd.DataFrame(database.APPOINTMENTS)
        st.dataframe(
            df[["id", "patient_id", "time", "status"]].tail(5),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.caption("No appointments booked yet.")

    # 3. Live Audit Stream
    st.subheader("🔒 Compliance Audit Log")
    if os.path.exists(utils.AUDIT_FILE):
        with open(utils.AUDIT_FILE, "r") as f:
            lines = f.readlines()
            # Show last 5 lines reversed
            for line in reversed(lines[-5:]):
                try:
                    entry = json.loads(line)
                    st.markdown(f"""
                    <div class="audit-entry">
                        <span style="color:gray">{entry['timestamp'].split('T')[1][:8]}</span> 
                        <b>{entry['action_type']}</b><br>
                        {str(entry['details'])[:50]}...
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    pass
    else:
        st.caption("Log file empty.")

# === LEFT COLUMN: Chat Interface ===
with col_chat:
    st.title("Clinical Workflow Orchestrator")
    st.caption("AI-Powered Care Coordination • HIPAA Compliant (Mock) • FHIR Standards")
    
    # Chat Container
    chat_container = st.container(height=600)
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            ### 👋 Welcome, Clinician.
            I can assist you with:
            - **Patient Search**: "Find patient Ravi Kumar"
            - **Eligibility Check**: "Check insurance for patient pat_001"
            - **Scheduling**: "Book a cardiology slot for Ravi next week"
            
            *Type your request below to begin.*
            """)
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🧑‍⚕️" if msg["role"] == "user" else "🤖"):
                st.write(msg["content"])
                
                # Render Tool Chains nicely
                if "tool_calls" in msg and msg["tool_calls"]:
                    with st.status("Workflow Execution Trace", state="complete", expanded=False):
                        for step in msg["tool_calls"]:
                            st.markdown(f"**🔹 Action:** `{step['tool']}`")
                            st.caption(f"Args: {step['args']}")
                            st.markdown(f"**🔸 Result:**")
                            try:
                                res_json = json.loads(step['result'])
                                st.json(res_json, expanded=False)
                            except:
                                st.code(step['result'])
                            st.divider()

    # Input Area
    if prompt := st.chat_input("Enter clinical request..."):
        # 1. User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user", avatar="🧑‍⚕️"):
                st.write(prompt)
        
        # 2. Agent Processing
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                message_placeholder = st.empty()
                status_container = st.status("Orchestrating Workflow...", expanded=True)
                
                try:
                    # Run Agent
                    result = st.session_state.agent.run(prompt)
                    
                    # Update Status with Steps
                    tool_calls = []
                    for step in result.get("steps", []):
                        if step["type"] == "tool_call":
                            tool_calls.append(step)
                            status_container.write(f"Executed `{step['tool']}`")
                            # Short delay for visual effect
                            time.sleep(0.3)
                    
                    status_container.update(label="Workflow Completed", state="complete", expanded=False)
                    
                    # Show Final Answer
                    message_placeholder.markdown(result["final_answer"])
                    
                    # Save History
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["final_answer"],
                        "tool_calls": tool_calls
                    })
                    
                    # Rerun to update sidebar/context immediately
                    st.rerun()
                    
                except Exception as e:
                    status_container.update(label="Workflow Failed", state="error")
                    st.error(f"System Error: {str(e)}")
