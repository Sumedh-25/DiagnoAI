"""
app.py
──────
DiagnoAI — Streamlit Frontend
Fully connected to backend + Groq API key validation.
"""

import sys
import os
import streamlit as st
from datetime import date

# ── Add backend to Python path ───────────────────────────────
BACKEND_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Backend")
sys.path.insert(0, os.path.abspath(BACKEND_PATH))

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DiagnoAI – DDR Generator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  LOAD API KEY FROM SECRETS
# ─────────────────────────────────────────────────────────────
def get_api_key() -> str:
    """
    Load Groq API key.
    Priority:
      1. Streamlit secrets (deployment)
      2. Session state (user entered in Settings)
    """
    # Try streamlit secrets first
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key and key.strip():
            return key.strip()
    except Exception:
        pass

    # Try session state (entered in Settings page)
    key = st.session_state.get("groq_api_key", "")
    if key and key.strip():
        return key.strip()

    return ""


# ─────────────────────────────────────────────────────────────
#  TEST API KEY FUNCTION
# ─────────────────────────────────────────────────────────────
def test_api_key(api_key: str) -> dict:
    """
    Tests if the Groq API key is valid by sending a simple request.
    Returns: { "valid": bool, "message": str }
    """
    try:
        from groq import Groq
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [{"role": "user", "content": "Say OK"}],
            max_tokens = 5,
        )
        if response.choices[0].message.content:
            return {"valid": True,  "message": "✅ Groq API key is valid and working!"}
        else:
            return {"valid": False, "message": "❌ API key returned empty response."}
    except Exception as e:
        return {"valid": False, "message": f"❌ API key error: {str(e)}"}


# ─────────────────────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%);
        color: #e2e8f0;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e2235 0%, #151825 100%);
        border-right: 1px solid #2d3748;
    }
    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 24px; margin-bottom: 20px;
    }
    .card-header {
        font-size: 14px; font-weight: 700; color: #f6ad55;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 10px; margin-bottom: 16px;
        letter-spacing: 0.5px; text-transform: uppercase;
    }
    .hero {
        background: linear-gradient(135deg, #f6ad55 0%, #ed8936 50%, #dd6b20 100%);
        border-radius: 16px; padding: 36px 40px; margin-bottom: 32px;
        position: relative; overflow: hidden;
    }
    .hero::before {
        content: ''; position: absolute; top: -40px; right: -40px;
        width: 180px; height: 180px; background: rgba(255,255,255,0.08);
        border-radius: 50%;
    }
    .hero-badge {
        display: inline-block; background: rgba(26,29,46,0.15);
        color: #1a1d2e; font-size: 11px; font-weight: 700;
        padding: 4px 12px; border-radius: 20px; margin-bottom: 14px;
        letter-spacing: 1px; text-transform: uppercase;
    }
    .hero-title {
        font-size: 30px; font-weight: 700; color: #1a1d2e;
        margin: 0; line-height: 1.3;
    }
    .hero-sub { font-size: 14px; color: rgba(26,29,46,0.72); margin-top: 8px; }

    .step-row { display: flex; gap: 12px; margin-bottom: 28px; }
    .step {
        flex: 1; background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 14px 10px; text-align: center;
    }
    .step.active { border-color: #f6ad55; background: rgba(246,173,85,0.08); }
    .step-num { font-size: 20px; font-weight: 700; color: #f6ad55; }
    .step-label { font-size: 11px; color: #a0aec0; margin-top: 4px; text-transform: uppercase; }

    .upload-zone {
        border: 2px dashed rgba(246,173,85,0.4); border-radius: 12px;
        padding: 20px; text-align: center; background: rgba(246,173,85,0.03); margin-bottom: 10px;
    }
    .upload-icon { font-size: 32px; margin-bottom: 6px; }
    .upload-title { font-size: 14px; font-weight: 600; color: #e2e8f0; }
    .upload-hint { font-size: 12px; color: #718096; margin-top: 4px; }

    .badge-success {
        display: inline-block; background: rgba(72,187,120,0.15); color: #68d391;
        border: 1px solid rgba(72,187,120,0.3); font-size: 12px; font-weight: 600;
        padding: 3px 10px; border-radius: 20px;
    }
    .badge-warning {
        display: inline-block; background: rgba(246,173,85,0.15); color: #f6ad55;
        border: 1px solid rgba(246,173,85,0.3); font-size: 12px; font-weight: 600;
        padding: 3px 10px; border-radius: 20px;
    }
    .badge-error {
        display: inline-block; background: rgba(252,129,129,0.15); color: #fc8181;
        border: 1px solid rgba(252,129,129,0.3); font-size: 12px; font-weight: 600;
        padding: 3px 10px; border-radius: 20px;
    }
    .info-box {
        background: rgba(66,153,225,0.08); border-left: 3px solid #4299e1;
        border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 12px 0;
        font-size: 13px; color: #90cdf4;
    }
    .warn-box {
        background: rgba(246,173,85,0.08); border-left: 3px solid #f6ad55;
        border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 12px 0;
        font-size: 13px; color: #fbd38d;
    }
    .success-box {
        background: rgba(72,187,120,0.08); border-left: 3px solid #48bb78;
        border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 12px 0;
        font-size: 13px; color: #9ae6b4;
    }
    .error-box {
        background: rgba(252,129,129,0.08); border-left: 3px solid #fc8181;
        border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 12px 0;
        font-size: 13px; color: #fed7d7;
    }
    .section-title {
        font-size: 12px; font-weight: 600; color: #718096;
        text-transform: uppercase; letter-spacing: 1px; margin: 16px 0 8px 0;
    }
    .api-status-ok {
        background: rgba(72,187,120,0.1); border: 1px solid rgba(72,187,120,0.3);
        border-radius: 8px; padding: 10px 16px; font-size: 13px; color: #68d391;
    }
    .api-status-fail {
        background: rgba(252,129,129,0.1); border: 1px solid rgba(252,129,129,0.3);
        border-radius: 8px; padding: 10px 16px; font-size: 13px; color: #fc8181;
    }
    .stButton > button {
        background: linear-gradient(135deg, #f6ad55, #ed8936) !important;
        color: #1a1d2e !important; font-weight: 700 !important;
        border: none !important; border-radius: 8px !important;
        padding: 12px 28px !important; font-size: 15px !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(246,173,85,0.4) !important;
    }
    .stButton > button:disabled {
        background: rgba(255,255,255,0.1) !important; color: #4a5568 !important;
    }
    label { color: #cbd5e0 !important; font-size: 13px !important; }
    hr { border-color: rgba(255,255,255,0.08) !important; }
    .footer {
        text-align: center; padding: 20px; color: #4a5568; font-size: 12px;
        border-top: 1px solid rgba(255,255,255,0.06); margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:20px 0 10px 0;'>
        <div style='font-size:40px;'>🏗️</div>
        <div style='font-size:20px; font-weight:700; color:#f6ad55; margin-top:6px;'>DiagnoAI</div>
        <div style='font-size:11px; color:#718096; letter-spacing:1px; text-transform:uppercase;'>DDR Report Generator</div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    # ── API Key Status in Sidebar ────────────────────────────
    api_key = get_api_key()
    if api_key:
        st.markdown("""
        <div class='api-status-ok'>
            🟢 &nbsp;<b>API Key Loaded</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='api-status-fail'>
            🔴 &nbsp;<b>API Key Missing</b><br>
            <small>Go to ⚙️ Settings to add key</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Navigation</div>", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠 Home", "📋 New Inspection", "⚙️ Settings", "📁 Report History", "ℹ️ About"],
        label_visibility="collapsed"
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Session Stats</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reports", st.session_state.get("report_count", 0))
    with col2:
        st.metric("Today", st.session_state.get("today_count", 0))

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:11px; color:#4a5568; text-align:center;'>
        Powered by Groq AI · UrbanRoof<br>v1.0.0
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  HOME PAGE
# ─────────────────────────────────────────────────────────────
if page == "🏠 Home":

    st.markdown("""
    <div class='hero'>
        <div class='hero-badge'>🤖 AI Powered · UrbanRoof</div>
        <div class='hero-title'>Detailed Diagnosis Report<br>Generator</div>
        <div class='hero-sub'>Upload Inspection + Thermal Reports → Get a professional DDR in seconds</div>
    </div>
    """, unsafe_allow_html=True)

    # API key warning on home if missing
    if not get_api_key():
        st.markdown("""
        <div class='warn-box'>
            ⚠️ <b>Groq API Key not found.</b>
            Go to <b>⚙️ Settings</b> page to add your key before generating reports.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class='step-row'>
        <div class='step active'><div class='step-num'>01</div><div class='step-label'>Upload Files</div></div>
        <div class='step active'><div class='step-num'>02</div><div class='step-label'>Fill Details</div></div>
        <div class='step active'><div class='step-num'>03</div><div class='step-label'>AI Processes</div></div>
        <div class='step active'><div class='step-num'>04</div><div class='step-label'>Download DDR</div></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class='card'>
            <div style='font-size:28px; margin-bottom:10px;'>🔍</div>
            <div style='font-weight:600; color:#f6ad55; margin-bottom:6px;'>Smart Extraction</div>
            <div style='font-size:13px; color:#a0aec0;'>Automatically extracts text and images from both inspection and thermal PDF reports.</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='card'>
            <div style='font-size:28px; margin-bottom:10px;'>🌡️</div>
            <div style='font-weight:600; color:#f6ad55; margin-bottom:6px;'>Thermal Analysis</div>
            <div style='font-size:13px; color:#a0aec0;'>Reads IR thermography data and maps cold zones to moisture-affected areas.</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class='card'>
            <div style='font-size:28px; margin-bottom:10px;'>📄</div>
            <div style='font-weight:600; color:#f6ad55; margin-bottom:6px;'>Professional DDR</div>
            <div style='font-size:13px; color:#a0aec0;'>Generates a structured Word document with images placed in correct sections.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
        💡 <b>How to use:</b> Click <b>"📋 New Inspection"</b> from the sidebar to start.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SETTINGS PAGE
# ─────────────────────────────────────────────────────────────
elif page == "⚙️ Settings":

    st.markdown("<h2 style='color:#f6ad55;'>⚙️ Settings</h2>", unsafe_allow_html=True)

    # ── API Key Section ──────────────────────────────────────
    st.markdown("<div class='card-header'>🔑 Groq API Key</div>", unsafe_allow_html=True)

    current_key = get_api_key()

    if current_key:
        st.markdown("""
        <div class='success-box'>
            ✅ API Key is loaded from <b>secrets.toml</b> or session.
        </div>
        """, unsafe_allow_html=True)
        masked = current_key[:8] + "..." + current_key[-4:]
        st.markdown(f"<p style='color:#718096; font-size:13px;'>Current key: <code>{masked}</code></p>",
                    unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='warn-box'>
            ⚠️ No API key found in secrets.toml. Enter it manually below.
        </div>
        """, unsafe_allow_html=True)

    manual_key = st.text_input(
        "Enter Groq API Key manually (for this session only)",
        type="password",
        placeholder="gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        help="This key will only be stored for this session. For permanent storage use secrets.toml"
    )

    col_save, col_test = st.columns(2)

    with col_save:
        if st.button("💾 Save Key to Session", use_container_width=True):
            if manual_key and manual_key.strip():
                st.session_state["groq_api_key"] = manual_key.strip()
                st.success("✅ API key saved to session!")
                st.rerun()
            else:
                st.error("❌ Please enter a valid API key.")

    with col_test:
        if st.button("🧪 Test API Key", use_container_width=True):
            test_key = manual_key.strip() if manual_key.strip() else current_key
            if not test_key:
                st.error("❌ No API key to test. Please enter one above.")
            else:
                with st.spinner("Testing API key..."):
                    result = test_api_key(test_key)
                if result["valid"]:
                    st.markdown(f"""
                    <div class='success-box'>
                        {result['message']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='error-box'>
                        {result['message']}
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='info-box'>
        🔒 For permanent storage add key to <b>.streamlit/secrets.toml</b>:<br>
        <code>GROQ_API_KEY = "your-key-here"</code><br><br>
        Get free key at: <b>https://console.groq.com</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Company Branding ─────────────────────────────────────
    st.markdown("<div class='card-header'>🏢 Company Branding</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Company Name",    value="UrbanRoof Private Limited")
        st.text_input("Company Email",   value="info@urbanroof.in")
    with col2:
        st.text_input("Company Phone",   value="+91-8925-805-805")
        st.text_input("Company Website", value="www.urbanroof.in")

    st.markdown("---")

    # ── Report Defaults ──────────────────────────────────────
    st.markdown("<div class='card-header'>📄 Report Defaults</div>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        st.selectbox("Default Output Format", ["Word Document (.docx)", "PDF (.pdf)", "Both"])
        st.selectbox("Report Language",       ["English", "Hindi", "Marathi"])
    with col4:
        st.selectbox("AI Model",              ["llama-3.3-70b-versatile (Recommended)", "llama-3.1-8b-instant"])
        st.slider("Max Images per Section",   1, 10, 5)

    if st.button("💾 Save All Settings"):
        st.success("✅ Settings saved successfully!")


# ─────────────────────────────────────────────────────────────
#  NEW INSPECTION PAGE
# ─────────────────────────────────────────────────────────────
elif page == "📋 New Inspection":

    st.markdown("<h2 style='color:#f6ad55; margin-bottom:4px;'>📋 New Inspection</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#718096; margin-bottom:24px;'>Fill all details and upload documents to generate a DDR report.</p>", unsafe_allow_html=True)

    # Check API key before showing form
    api_key = get_api_key()
    if not api_key:
        st.markdown("""
        <div class='error-box'>
            🔴 <b>Groq API Key not found!</b><br>
            Please go to <b>⚙️ Settings</b> page and add your API key first.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── SECTION 1: Property Info ─────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🏠 Section 1 · Property Information</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        customer_name    = st.text_input("Customer Name *",         placeholder="e.g. Rahul Sharma")
        property_address = st.text_area("Property Address *",       placeholder="Flat No, Building, Street, City, PIN", height=90)
        property_type    = st.selectbox("Property Type *",          ["Flat / Apartment", "Row House", "Bungalow", "Villa", "Commercial", "Other"])
        floors           = st.number_input("Number of Floors *",    min_value=1, max_value=50, value=1)
    with col2:
        mobile           = st.text_input("Mobile Number *",         placeholder="+91 XXXXXXXXXX")
        email            = st.text_input("Email Address",           placeholder="client@email.com")
        property_age     = st.number_input("Property Age (Years)*", min_value=0, max_value=100, value=5)
        inspection_date  = st.date_input("Inspection Date *",       value=date.today())

    col3, col4 = st.columns(2)
    with col3:
        inspected_by     = st.text_input("Inspected By *",          placeholder="Inspector Name(s)")
        inspection_time  = st.time_input("Inspection Time *")
    with col4:
        prev_audit       = st.selectbox("Previous Structural Audit Done?", ["No", "Yes", "Not Sure"])
        prev_repair      = st.selectbox("Previous Repair Work Done?",      ["No", "Yes", "Not Sure"])

    # ── SECTION 2: Upload Documents ──────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>📎 Section 2 · Upload Documents</div>", unsafe_allow_html=True)

    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.markdown("""
        <div class='upload-zone'>
            <div class='upload-icon'>📋</div>
            <div class='upload-title'>Inspection Report PDF</div>
            <div class='upload-hint'>Site observations, checklist, area-wise photos</div>
        </div>""", unsafe_allow_html=True)
        inspection_pdf = st.file_uploader(
            "Upload Inspection Report", type=["pdf"], key="insp_pdf",
            help="Main inspection report with area-wise observations and photographs"
        )
        if inspection_pdf:
            st.markdown(f"<span class='badge-success'>✅ {inspection_pdf.name} · {round(inspection_pdf.size/1024,1)} KB</span>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-warning'>⏳ Awaiting upload</span>", unsafe_allow_html=True)

    with col_u2:
        st.markdown("""
        <div class='upload-zone'>
            <div class='upload-icon'>🌡️</div>
            <div class='upload-title'>Thermal Imaging Report PDF</div>
            <div class='upload-hint'>IR thermography images and temperature readings</div>
        </div>""", unsafe_allow_html=True)
        thermal_pdf = st.file_uploader(
            "Upload Thermal Report", type=["pdf"], key="therm_pdf",
            help="Thermal report with hotspot/coldspot temperature data per area"
        )
        if thermal_pdf:
            st.markdown(f"<span class='badge-success'>✅ {thermal_pdf.name} · {round(thermal_pdf.size/1024,1)} KB</span>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-warning'>⏳ Awaiting upload</span>", unsafe_allow_html=True)

    # ── SECTION 3: Impacted Areas ─────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🗺️ Section 3 · Impacted Areas</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#a0aec0; font-size:13px;'>Select all areas with reported issues:</p>", unsafe_allow_html=True)

    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
    with col_a1:
        area_hall       = st.checkbox("🛋️ Hall / Living Room")
        area_bedroom    = st.checkbox("🛏️ Bedroom")
        area_master_bed = st.checkbox("🛏️ Master Bedroom")
    with col_a2:
        area_kitchen    = st.checkbox("🍳 Kitchen")
        area_com_bath   = st.checkbox("🚿 Common Bathroom")
        area_mas_bath   = st.checkbox("🚿 Master Bathroom")
    with col_a3:
        area_balcony    = st.checkbox("🌿 Balcony")
        area_parking    = st.checkbox("🚗 Parking Area")
        area_terrace    = st.checkbox("🏠 Terrace")
    with col_a4:
        area_ext_wall   = st.checkbox("🧱 External Wall")
        area_staircase  = st.checkbox("🪜 Staircase")
        area_other      = st.checkbox("📍 Other")

    other_area_text = ""
    if area_other:
        other_area_text = st.text_input("Specify Other Area", placeholder="e.g. Store Room, Garage...")

    # ── SECTION 4: WC / Bathroom Checklist ───────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🚿 Section 4 · WC / Bathroom Checklist</div>", unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("<div class='section-title'>Negative Side — Impacted Area</div>", unsafe_allow_html=True)
        wc_leak_adj    = st.selectbox("Leakage at adjacent walls",          ["No Leakage","Dampness","Seepage / Mild Leakage","Live Leakage"])
        wc_leak_below  = st.selectbox("Leakage below WC floor",             ["No Leakage","Dampness","Seepage / Mild Leakage","Live Leakage"])
        wc_leak_during = st.selectbox("Leakage occurs during",              ["All Time","Monsoon Only","Not Sure"])
        wc_conc_plumb  = st.selectbox("Leakage due to concealed plumbing?", ["Yes","No","Not Sure"])
        wc_nahani_dmg  = st.selectbox("Leakage due to damaged Nahani trap / Brickbat coba?", ["Yes","No","Not Sure"])
    with col_b2:
        st.markdown("<div class='section-title'>Positive Side — Source Area</div>", unsafe_allow_html=True)
        wc_tile_gaps   = st.selectbox("Gaps / Blackish dirt in tile joints?",["Yes","No","Not Sure"])
        wc_nahani_gaps = st.selectbox("Gaps around Nahani Trap joints?",     ["Yes","No","Not Sure"])
        wc_tiles_brkn  = st.selectbox("Tiles broken / loose anywhere?",      ["Yes","No","Not Sure"])
        wc_plumb_loose = st.selectbox("Loose plumbing joints / rust?",       ["Yes","No","Not Sure"])
        wc_tile_type   = st.selectbox("Type of tile",                        ["Moderate","Ceramic","Marble","Stone Tile","Porcelain","Concrete","Not Sure"])

    # ── SECTION 5: External Wall ──────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🧱 Section 5 · External Wall Checklist</div>", unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("<div class='section-title'>Negative Side — Interior</div>", unsafe_allow_html=True)
        ext_leak_int   = st.selectbox("Leakage at interior side",           ["No Leakage","Dampness","Seepage / Mild Leakage","Live Leakage"], key="eli")
        ext_leak_dur   = st.selectbox("Leakage during",                     ["Monsoon","All Time","Not Sure"], key="eld")
        ext_conc_plumb = st.selectbox("Leakage due to concealed plumbing?", ["Yes","No","Not Sure"], key="ecp")
        ext_wc_balc    = st.selectbox("Internal WC / Bath / Balcony leakage?", ["Yes","No","Not Sure"])
    with col_c2:
        st.markdown("<div class='section-title'>Positive Side — Exterior</div>", unsafe_allow_html=True)
        ext_paint_type = st.selectbox("Existing paint type",                ["Not Sure","No Paint","White Wash","Cement Paint","Semi-Acrylic Emulsion","Acrylic Emulsion","Premium Waterproof Acrylic","Textured Paint"])
        ext_cracks     = st.selectbox("Cracks on external surface?",        ["N/A","No","Moderate","Severe"])
        ext_algae      = st.selectbox("Algae / fungus / moss?",             ["N/A","No","Moderate","Severe"])
        ext_plumb_crk  = st.selectbox("External plumbing pipes cracked?",   ["N/A","No","Moderate","Severe"])

    # ── SECTION 6: RCC Structural ─────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🏗️ Section 6 · Structural Condition of RCC Members</div>", unsafe_allow_html=True)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        rcc_cracks     = st.selectbox("Cracks on RCC Column and Beam",      ["N/A","Good","Moderate","Poor"])
        rcc_rust       = st.selectbox("Rust marks on RCC Beam and Column",  ["N/A","Good","Moderate","Poor"])
        rcc_spalling   = st.selectbox("Corrosion / Spalling / Exposed reinforcement", ["N/A","Good","Moderate","Poor"])
    with col_d2:
        rcc_expansion  = st.selectbox("Expansion joints condition",         ["N/A","Good","Moderate","Poor"])
        rcc_separation = st.selectbox("Separation cracks at beam-column junction", ["N/A","Good","Moderate","Poor"])
        rcc_ohwt       = st.selectbox("Leakage from overhead water tank",   ["N/A","Good","Moderate","Poor"])

    # ── SECTION 7: Plaster / Paint ────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🪣 Section 7 · Plaster / Paint Condition</div>", unsafe_allow_html=True)

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        plaster_patch  = st.selectbox("Patchwork plaster required?",        ["N/A","Good","Moderate","Poor"])
        plaster_full   = st.selectbox("Entire re-plaster required?",        ["N/A","Good","Moderate","Poor"])
        plaster_loose  = st.selectbox("Loose plaster / hollow sound?",      ["N/A","Good","Moderate","Poor"])
    with col_e2:
        paint_chalk    = st.selectbox("Chalking and flaking in paint?",     ["N/A","Good","Moderate","Poor"])
        paint_algae    = st.selectbox("Algae / fungus / moss on wall?",     ["N/A","Good","Moderate","Poor"])
        paint_bird     = st.selectbox("Bird droppings on wall / Chajja?",   ["N/A","Good","Moderate","Poor"])

    # ── SECTION 8: Thermal Details ────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>🌡️ Section 8 · Thermal Camera Details</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        📌 These will be <b>auto-filled by AI</b> from your thermal PDF. You may override manually.
    </div>""", unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        thermal_device   = st.text_input("Thermal Camera Device",      value="Bosch GTC 400C Professional")
        thermal_emiss    = st.text_input("Emissivity",                 value="0.94")
    with col_f2:
        thermal_ref_temp = st.text_input("Reflected Temperature (°C)", placeholder="e.g. 23")
        thermal_notes    = st.text_area("Additional Thermal Notes",    placeholder="Any special thermal observations...", height=70)

    # ── SECTION 9: Output Settings ────────────────────────────
    st.markdown("---")
    st.markdown("<div class='card-header'>⚙️ Section 9 · DDR Output Settings</div>", unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        report_format  = st.selectbox("Output Format",               ["Word Document (.docx)", "PDF (.pdf)", "Both"])
        severity_level = st.selectbox("Overall Severity Assessment", ["Auto Detect by AI","Low","Moderate","High","Critical"])
        report_lang    = st.selectbox("Report Language",             ["English","Hindi","Marathi"])
    with col_g2:
        include_images    = st.checkbox("Include Site Photos in Report",    value=True)
        include_thermal   = st.checkbox("Include Thermal Images in Report", value=True)
        include_checklist = st.checkbox("Include Checklist Summary",        value=True)
        include_disclaimer= st.checkbox("Include Legal Disclaimer",         value=True)
        include_summary   = st.checkbox("Include Summary Table",            value=True)

    additional_notes = st.text_area(
        "Special Instructions for AI (Optional)",
        placeholder="e.g. Focus on kitchen dampness, highlight urgent items first...",
        height=80
    )

    # ── GENERATE BUTTON ───────────────────────────────────────
    st.markdown("---")

    # Build selected areas list
    selected_areas = []
    if area_hall:       selected_areas.append("Hall / Living Room")
    if area_bedroom:    selected_areas.append("Bedroom")
    if area_master_bed: selected_areas.append("Master Bedroom")
    if area_kitchen:    selected_areas.append("Kitchen")
    if area_com_bath:   selected_areas.append("Common Bathroom")
    if area_mas_bath:   selected_areas.append("Master Bathroom")
    if area_balcony:    selected_areas.append("Balcony")
    if area_parking:    selected_areas.append("Parking Area")
    if area_terrace:    selected_areas.append("Terrace")
    if area_ext_wall:   selected_areas.append("External Wall")
    if area_staircase:  selected_areas.append("Staircase")
    if area_other and other_area_text:
        selected_areas.append(other_area_text)

    # Validation
    all_filled = (
        inspection_pdf is not None and
        thermal_pdf    is not None and
        bool(customer_name.strip()) and
        bool(property_address.strip()) and
        bool(api_key)
    )

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:

        if not all_filled:
            missing = []
            if not customer_name.strip():    missing.append("Customer Name")
            if not property_address.strip(): missing.append("Property Address")
            if inspection_pdf is None:       missing.append("Inspection PDF")
            if thermal_pdf    is None:       missing.append("Thermal PDF")
            if not api_key:                  missing.append("Groq API Key (go to Settings)")
            st.markdown(f"""
            <div class='warn-box'>
                ⚠️ Please complete: <b>{", ".join(missing)}</b>
            </div>""", unsafe_allow_html=True)

        generate_btn = st.button(
            "🚀  Generate DDR Report",
            disabled=not all_filled,
            use_container_width=True
        )

        # ── GENERATE LOGIC ────────────────────────────────────
        if generate_btn:

            # Collect all property info
            property_info = {
                "customer_name":    customer_name.strip(),
                "property_address": property_address.strip(),
                "property_type":    property_type,
                "floors":           floors,
                "property_age":     property_age,
                "inspection_date":  str(inspection_date),
                "inspected_by":     inspected_by.strip(),
                "prev_audit":       prev_audit,
                "prev_repair":      prev_repair,
                "selected_areas":   ", ".join(selected_areas) if selected_areas else "Not specified",
                "wc_leak_adj":      wc_leak_adj,
                "wc_leak_below":    wc_leak_below,
                "wc_leak_during":   wc_leak_during,
                "wc_conc_plumb":    wc_conc_plumb,
                "wc_nahani_dmg":    wc_nahani_dmg,
                "wc_tile_gaps":     wc_tile_gaps,
                "wc_nahani_gaps":   wc_nahani_gaps,
                "wc_tiles_brkn":    wc_tiles_brkn,
                "wc_plumb_loose":   wc_plumb_loose,
                "wc_tile_type":     wc_tile_type,
                "ext_leak_int":     ext_leak_int,
                "ext_leak_dur":     ext_leak_dur,
                "ext_conc_plumb":   ext_conc_plumb,
                "ext_wc_balc":      ext_wc_balc,
                "ext_paint_type":   ext_paint_type,
                "ext_cracks":       ext_cracks,
                "ext_algae":        ext_algae,
                "ext_plumb_crk":    ext_plumb_crk,
                "rcc_cracks":       rcc_cracks,
                "rcc_rust":         rcc_rust,
                "rcc_spalling":     rcc_spalling,
                "rcc_expansion":    rcc_expansion,
                "rcc_separation":   rcc_separation,
                "rcc_ohwt":         rcc_ohwt,
                "plaster_patch":    plaster_patch,
                "plaster_full":     plaster_full,
                "plaster_loose":    plaster_loose,
                "paint_chalk":      paint_chalk,
                "paint_algae":      paint_algae,
                "paint_bird":       paint_bird,
                "thermal_device":   thermal_device,
                "thermal_emiss":    thermal_emiss,
                "thermal_ref_temp": thermal_ref_temp,
                "thermal_notes":    thermal_notes,
                "severity_level":   severity_level,
                "additional_notes": additional_notes,
            }

            # Progress UI
            progress = st.progress(0)
            status   = st.empty()

            try:
                # Import backend
                from main import generate_ddr_report

                status.markdown("<div class='info-box'>📄 Reading Inspection Report PDF...</div>",
                                unsafe_allow_html=True)
                progress.progress(15)

                status.markdown("<div class='info-box'>🌡️ Reading Thermal Imaging Report PDF...</div>",
                                unsafe_allow_html=True)
                progress.progress(30)

                status.markdown("<div class='info-box'>🖼️ Extracting photographs and thermal images...</div>",
                                unsafe_allow_html=True)
                progress.progress(45)

                status.markdown("<div class='info-box'>🤖 Groq AI is analyzing and merging data...</div>",
                                unsafe_allow_html=True)
                progress.progress(60)

                # ── CALL BACKEND ──────────────────────────────
                result = generate_ddr_report(
                    inspection_pdf_bytes = inspection_pdf.read(),
                    thermal_pdf_bytes    = thermal_pdf.read(),
                    property_info        = property_info,
                    groq_api_key         = api_key,
                )

                progress.progress(85)
                status.markdown("<div class='info-box'>📝 Building professional Word document...</div>",
                                unsafe_allow_html=True)
                progress.progress(100)

                # ── HANDLE RESULT ─────────────────────────────
                if result["success"]:
                    status.markdown("<div class='success-box'>✅ DDR Report generated successfully!</div>",
                                    unsafe_allow_html=True)
                    st.balloons()

                    # Update session stats
                    st.session_state["report_count"] = st.session_state.get("report_count", 0) + 1
                    st.session_state["today_count"]  = st.session_state.get("today_count",  0) + 1

                    # Show extraction stats
                    stats = result.get("stats", {})
                    st.markdown("---")
                    st.markdown("<div class='card-header'>📊 Extraction Statistics</div>",
                                unsafe_allow_html=True)
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("Inspection Pages",  stats.get("inspection_pages",  0))
                    sc2.metric("Thermal Pages",     stats.get("thermal_pages",     0))
                    sc3.metric("Inspection Images", stats.get("inspection_images", 0))
                    sc4.metric("Thermal Images",    stats.get("thermal_images",    0))

                    # Show non-fatal errors if any
                    if result.get("errors"):
                        st.markdown("<div class='warn-box'>⚠️ Some minor issues (report still generated):<br>" +
                                    "<br>".join(result["errors"][:5]) + "</div>",
                                    unsafe_allow_html=True)

                    # Download buttons
                    st.markdown("---")
                    fname = customer_name.strip().replace(" ", "_")
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label     = "📥 Download Word Report (.docx)",
                            data      = result["docx_bytes"],
                            file_name = f"DDR_{fname}_{date.today()}.docx",
                            mime      = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    with col_dl2:
                        st.info("PDF version coming soon. Download Word and save as PDF.")

                else:
                    status.markdown("<div class='error-box'>❌ Report generation failed.</div>",
                                    unsafe_allow_html=True)
                    for err in result.get("errors", []):
                        st.error(err)

            except ImportError as e:
                st.error(f"❌ Backend import error: {e}. Make sure all backend files are in the Backend/ folder.")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                progress.progress(0)


# ─────────────────────────────────────────────────────────────
#  REPORT HISTORY PAGE
# ─────────────────────────────────────────────────────────────
elif page == "📁 Report History":
    st.markdown("<h2 style='color:#f6ad55;'>📁 Report History</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class='card' style='text-align:center; padding:60px;'>
        <div style='font-size:48px; margin-bottom:16px;'>📭</div>
        <div style='font-size:18px; font-weight:600; color:#e2e8f0;'>No Reports Yet</div>
        <div style='font-size:13px; color:#718096; margin-top:8px;'>
            Go to New Inspection to generate your first DDR report.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  ABOUT PAGE
# ─────────────────────────────────────────────────────────────
elif page == "ℹ️ About":
    st.markdown("<h2 style='color:#f6ad55;'>ℹ️ About DiagnoAI</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class='card'>
        <div style='font-size:14px; color:#e2e8f0; line-height:1.9;'>
            <b style='color:#f6ad55;'>DiagnoAI</b> is an AI-powered Detailed Diagnosis Report (DDR) generator
            built for <b>UrbanRoof Private Limited</b>. It converts raw site inspection data into
            structured, client-ready reports automatically using Groq AI.
        </div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class='card'>
            <div class='card-header'>🛠️ Tech Stack</div>
            <div style='font-size:13px; color:#a0aec0; line-height:2.2;'>
                🐍 Python 3.11<br>
                🎨 Streamlit Framework<br>
                🤖 Groq AI — LLaMA 3.3 70B<br>
                📄 PyMuPDF — PDF Parsing<br>
                📝 python-docx — Report Generation<br>
                🖼️ Pillow — Image Processing<br>
                ☁️ Streamlit Cloud — Deployment
            </div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='card'>
            <div class='card-header'>📋 DDR Sections Generated</div>
            <div style='font-size:13px; color:#a0aec0; line-height:2.2;'>
                1️⃣ Property Issue Summary<br>
                2️⃣ Area-wise Observations<br>
                3️⃣ Probable Root Cause<br>
                4️⃣ Severity Assessment<br>
                5️⃣ Recommended Actions<br>
                6️⃣ Additional Notes<br>
                7️⃣ Missing / Unclear Information
            </div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class='footer'>
    DiagnoAI · Built for UrbanRoof Private Limited · Powered by Groq AI · 2024
</div>
""", unsafe_allow_html=True)