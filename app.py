from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Intelligent Traffic System",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
VIDEOS = {
    "Normal Traffic": "normal_traffic.mp4",
    "Rainy Traffic": "rainy_traffic.mp4",
    "Vehicle Collision": "vehicle_collision.mp4",
}

st.markdown("""
<style>
:root {
    --bg: #101D29;
    --panel: #1B2C39;
    --panel2: #213644;
    --stroke: #344957;
    --mint: #66D4BD;
    --coral: #FFAD85;
    --text: #F1F5F5;
    --muted: #9AB0BA;
}
html, body, [class*="css"] {
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
}
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
    background: #142330;
    border-right: 1px solid var(--stroke);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.7rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    color: var(--muted);
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: .55rem .65rem;
    border-radius: .6rem;
    transition: background .15s;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #223744; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #23443f;
    border: 1px solid #477e70;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: #9df2d5; }
.block-container { max-width: 1480px; padding-top: 2.5rem; padding-bottom: 4rem; }
h1, h2, h3 { font-family: Bahnschrift, "Arial Narrow", "Segoe UI", sans-serif; letter-spacing: .025em; }
h1 { color: var(--text); }
p, label { color: var(--text); }
[data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--stroke); border-radius: 14px; padding: 1.2rem; }
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricValue"] { color: var(--text); }
[data-testid="stSelectbox"] > div > div { background-color: var(--panel); border-color: var(--stroke); }
[data-testid="stVideo"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--stroke); }
[data-testid="stAlert"] { border-radius: 12px; }
.stButton > button { border-radius: 10px; background: var(--mint); border: 0; color: #102b2b; font-weight: 700; }
.stButton > button:hover { background: #91eed6; color: #102b2b; }
.rosh-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; }
.rosh-mark { display: grid; place-items: center; width: 44px; height: 44px; border: 1px solid #448473; background: #173b3b; border-radius: 13px; color: var(--mint); font: 800 27px Bahnschrift, sans-serif; }
.rosh-word { font: 700 25px Bahnschrift, sans-serif; letter-spacing: .085em; color: var(--text); }
.rosh-caption { color: var(--muted); font: 600 10px "Segoe UI", sans-serif; letter-spacing: .2em; }
.eyebrow { color: var(--mint); font-size: 11px; font-weight: 700; letter-spacing: .21em; text-transform: uppercase; }
.hero-title { font: 700 clamp(29px, 3vw, 43px) Bahnschrift, "Segoe UI", sans-serif; letter-spacing: .012em; color: var(--text); margin: 7px 0; }
.hero-sub { color: var(--muted); font-size: 14px; margin-bottom: 1.5rem; }
.status-dot { display:inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--mint); margin-right: 7px; box-shadow: 0 0 0 4px #66d4bd20; }
.status-pill { display:inline-block; font-size: 11px; color: #a4f0d7; background: #1a433b; border: 1px solid #397b69; border-radius: 30px; padding: 7px 11px; }
.metric-card { background: var(--panel); border: 1px solid var(--stroke); border-radius: 14px; min-height: 115px; padding: 19px; margin-bottom: 1.2rem; }
.metric-label { font-size: 10px; letter-spacing: .13em; font-weight: 700; color: var(--muted); }
.metric-value { margin: 8px 0 0; font: 700 34px Bahnschrift, sans-serif; color: var(--text); }
.metric-value.mint { color: var(--mint); }
.metric-value.coral { color: var(--coral); }
.section-header { font: 700 18px Bahnschrift, sans-serif; letter-spacing: .05em; color: var(--text); margin: 0 0 12px; }
.panel { background: var(--panel); border: 1px solid var(--stroke); padding: 20px; border-radius: 14px; min-height: 145px; margin: 8px 0 15px; }
.panel .small { font-size: 11px; letter-spacing: .13em; font-weight: 700; color: var(--muted); }
.panel .large { margin-top: 14px; color: var(--text); font-size: 16px; font-weight: 600; }
.panel .note { margin-top: 7px; color: var(--muted); font-size: 12px; line-height: 1.55; }
.panel .accent { color: var(--coral); }
.sidebar-footer { color: var(--muted); font-size: 11px; padding-top: 18px; border-top: 1px solid var(--stroke); margin-top: 28px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div class="rosh-brand">
      <div class="rosh-mark">R</div>
      <div><div class="rosh-word">Insert name of website here</div><div class="rosh-caption">Intelligent Traffic System</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<span class="status-pill"><span class="status-dot"></span>LOCAL SYSTEM ONLINE</span>', unsafe_allow_html=True)
    st.write("")
    page = st.radio("WORKSPACE", ["Dashboard", "AI Assistant", "Incident Logs", "Settings"], label_visibility="visible")
    st.markdown('<div class="sidebar-footer"> PROTOTYPE 01<br>LOCAL ENVIRONMENT · CPU-FIRST</div>', unsafe_allow_html=True)

st.markdown('<div class="eyebrow">PLATFORM FOR TRAFFIC DATA ANALYTICS</div>', unsafe_allow_html=True)

if page == "Dashboard":
    st.markdown('<div class="hero-title">Traffic Operations Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">A centralized intelligent monitoring workspace.</div>', unsafe_allow_html=True)

    cards = [
        ("VIDEO SOURCES", "03", ""),
        ("VEHICLES DETECTED", "—", ""),
        ("ACTIVE INCIDENTS", "00", "coral"),
        ("AI ANALYSIS", "OFFLINE", "mint"),
    ]
    cols = st.columns(4, gap="medium")
    for col, (label, value, color) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value {color}">{value}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Camera Monitor</div>', unsafe_allow_html=True)
    video_col, info_col = st.columns([2.1, 1], gap="large")
    with video_col:
        scenario = st.selectbox("ACTIVE VIDEO SOURCE", list(VIDEOS.keys()), key="selected_scenario")
        video_path = BASE_DIR / "videos" / VIDEOS[scenario]
        if video_path.is_file():
            st.video(str(video_path))
        else:
            st.info(f"Video not loaded. Place {VIDEOS[scenario]} in the videos folder.")
        st.caption("Recorded footage · Local playback · AI processing not yet connected")

    with info_col:
        st.markdown('<div class="panel"><div class="small">SCENE INTELLIGENCE</div><div class="large">Analysis pending</div><div class="note">Qwen visual reasoning will summarize weather, road conditions, and traffic flow here.</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="small">INCIDENT MONITOR</div><div class="large">No verified incidents</div><div class="note">Collision alerts will appear here after the detection pipeline is connected.</div></div>', unsafe_allow_html=True)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="section-header">Detection Pipeline</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="small">YOLO / OPENCV</div><div class="large">Awaiting integration</div><div class="note">Vehicle counts and tracking results will populate this panel from actual video analysis.</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-header">Latest Activity</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="small">SYSTEM EVENT LOG</div><div class="large">Dashboard initialized</div><div class="note">No model-generated events have been recorded.</div></div>', unsafe_allow_html=True)

elif page == "AI Assistant":
    st.markdown('<div class="hero-title">Qwen Traffic Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">A dedicated workspace for evidence-based scene questions.</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="small">CONNECTION STATUS</div><div class="large">Not connected</div><div class="note">The local Qwen model and chat interface will be integrated in the next phase.</div></div>', unsafe_allow_html=True)

elif page == "Incident Logs":
    st.markdown('<div class="hero-title">Incident Registry</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Review, acknowledge, and audit detected traffic events.</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="small">REGISTERED EVENTS</div><div class="large">No incidents recorded</div><div class="note">Future records will contain evidence timestamps, severity, and operator actions.</div></div>', unsafe_allow_html=True)

elif page == "Settings":
    st.markdown('<div class="hero-title">System Configuration</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Local-first processing with modest CPU and memory requirements.</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="small">PROCESSING PROFILE</div><div class="large">CPU-first · Windows local</div><div class="note">Recommended models: YOLO11n for vehicles and Qwen3-VL 2B for sampled-frame reasoning. Model integration pending.</div></div>', unsafe_allow_html=True)
