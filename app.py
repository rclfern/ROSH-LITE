"""Traffic Data Analytics Prototype — offline-friendly Streamlit dashboard.

This release is a polished UI with synthetic demo statistics. It does NOT
perform YOLO analysis, measure actual traffic speeds, or inspect video frames.
The optional local-agent text chat can contact a user's own Ollama installation.
"""

from __future__ import annotations

import csv
import html
import io
import json
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
VIDEOS = ROOT / "videos"
LOCAL_API = "http://127.0.0.1:11434"

st.set_page_config(
    page_title="Traffic Data Analytics Prototype",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Everything displayed as a metric, sensor, incident, trend, or location below
# is synthetic sample content created to demonstrate the UI. In particular,
# these numbers MUST NOT be interpreted as live government/city feeds.
SCENARIOS = {
    "Normal traffic": {
        "video": "normal_traffic.mp4",
        "short": "Clear and moving",
        "weather": "Clear / dry road",
        "assessment": "No event suggested",
        "recommendation": "Continue routine observation.",
        "volume": 24891,
        "average_speed": 34.5,
        "congested": 8.4,
        "incidents": 0,
        "trend": [3100, 2650, 2920, 3900, 5700, 8500, 12200, 16300, 22000, 24891, 23600, 20500, 19500],
    },
    "Rainy traffic": {
        "video": "rainy_traffic.mp4",
        "short": "Wet-road conditions",
        "weather": "Rain / wet pavement",
        "assessment": "Weather advisory suggested",
        "recommendation": "Advise caution and review visibility.",
        "volume": 21640,
        "average_speed": 22.8,
        "congested": 24.1,
        "incidents": 1,
        "trend": [3200, 2800, 3300, 4100, 6100, 9200, 14200, 19700, 21640, 20100, 18900, 16600, 16000],
    },
    "Vehicle collision": {
        "video": "vehicle_collision.mp4",
        "short": "Potential incident",
        "weather": "Not determined",
        "assessment": "Possible collision — verify footage",
        "recommendation": "Flag for operator review before dispatch.",
        "volume": 19480,
        "average_speed": 12.1,
        "congested": 38.6,
        "incidents": 1,
        "trend": [3100, 2400, 2800, 4200, 6600, 10200, 15700, 19000, 19480, 15900, 13100, 12000, 12700],
    },
}

# Deliberately labeled as fictional demo records.
INCIDENTS = [
    {"id": "INC-001", "type": "Collision", "road": "Commonwealth Avenue", "place": "Near Philcoa, Quezon City", "delay": "+6.4 min", "time": "08:19", "severity": "high", "detail": "Possible two-vehicle contact; unverified demo event."},
    {"id": "INC-002", "type": "Roadworks", "road": "Batasan–San Mateo Road", "place": "Near Loyola Grand Villas", "delay": "+2.1 min", "time": "07:50", "severity": "medium", "detail": "Example lane closure entered for the dashboard demo."},
    {"id": "INC-003", "type": "Disabled vehicle", "road": "Mindanao Avenue", "place": "Near Visayas Avenue", "delay": "+1.2 min", "time": "06:24", "severity": "low", "detail": "Example stopped-vehicle report entered for the dashboard demo."},
]

CORRIDORS = [
    {"road": "EDSA (QC)", "speed": 12.1, "delta": "+6.4", "level": 83, "status": "Heavy", "severity": "high"},
    {"road": "Commonwealth Ave", "speed": 18.6, "delta": "+2.1", "level": 59, "status": "Moderate", "severity": "medium"},
    {"road": "Mindanao Avenue", "speed": 23.8, "delta": "+1.4", "level": 43, "status": "Moderate", "severity": "medium"},
    {"road": "Quirino Highway", "speed": 31.2, "delta": "+0.3", "level": 19, "status": "Clear", "severity": "low"},
    {"road": "Tandang Sora Ave", "speed": 34.5, "delta": "+1.1", "level": 15, "status": "Clear", "severity": "low"},
]

NAV_ITEMS = ["Overview", "Video sources", "Corridors", "Incidents", "Reports", "Local agent", "Settings"]

if "page" not in st.session_state:
    st.session_state.page = "Overview"
if "scenario" not in st.session_state:
    st.session_state.scenario = "Normal traffic"
if "reviewed" not in st.session_state:
    st.session_state.reviewed = set()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ollama_model" not in st.session_state:
    st.session_state.ollama_model = "qwen3-vl:2b"


CSS = r"""
<style>
:root { --navy:#10252d; --navy2:#17343a; --teal:#168b85; --mint:#dff4ee; --ink:#1b2936;
        --muted:#728391; --paper:#f4f7f8; --line:#e2e9ed; --orange:#f29b45; --red:#e95b4f; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], button, input, textarea {
  font-family:"Aptos", "Segoe UI", sans-serif; }
[data-testid="stAppViewContainer"] {background:linear-gradient(125deg,#f8fafb 0%,#f0f4f6 100%);}
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1600px; padding-top:1.25rem; padding-bottom:2rem; padding-left:2.05rem; padding-right:2.05rem; }
[data-testid="stSidebar"] { background:linear-gradient(178deg,#10242d,#132f38 78%,#10252d) !important;
  border-right:1px solid #294650; }
[data-testid="stSidebar"] > div:first-child { padding:1.1rem .85rem 1rem; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {color:#d5e4e9;}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {gap:4px;}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {
  padding:.57rem .75rem; border-radius:9px; transition:background .16s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {background:#213f48;}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
  background:linear-gradient(90deg,#22545a,#24434e); box-shadow:inset 3px 0 #54cbbb;}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {
  color:#fff !important;font-weight:650;}
[data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] {display:none;}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {display:none;}
.sidebar-brand {padding:.7rem .65rem 1.7rem;border-bottom:1px solid #2b4950;margin-bottom:1.1rem;}
.brand-row {display:flex;align-items:center;gap:12px;}
.brand-symbol {display:flex;align-items:center;gap:4px;height:35px;}
.brand-symbol span {width:5px;border-radius:3px;background:#62d7bd;display:inline-block;}
.brand-symbol span:nth-child(1){height:22px;}.brand-symbol span:nth-child(2){height:32px;}.brand-symbol span:nth-child(3){height:15px;}
.brand-name {color:#f4fcfc;font-size:17px;font-weight:760;letter-spacing:-.4px;line-height:1.15;}
.brand-sub {color:#89aab3;font-size:10px;letter-spacing:1.3px;margin-top:9px;text-transform:uppercase;}
.sidebar-overline {color:#83a4af;font-size:10px;letter-spacing:1.65px;font-weight:750;margin:12px 10px 6px;}
.sidebar-workspace {color:#f3fbfa;border:1px solid #31515a;background:#1c3a43;border-radius:9px;
  padding:11px 12px;margin:0 7px 20px;font-size:13px;font-weight:600;}
.sidebar-footer {margin:1.4rem .35rem .5rem;padding:14px;border:1px solid #31505a;border-radius:12px;
  color:#c9dfe2;background:rgba(255,255,255,.025);font-size:12px;line-height:1.65;}
.sidebar-footer b {color:#b6e8dc;}
.sidebar-footer .dot {display:inline-block;width:7px;height:7px;background:#36bc9b;border-radius:50%;margin-right:7px;}
.side-note {font-size:10px;color:#8eaab3;margin:13px 9px 0;line-height:1.65;}
.topbar {background:#fff;border:1px solid #e5ebee;border-radius:10px;padding:13px 19px;
  color:#718292;font-size:12px;display:flex;justify-content:space-between;align-items:center;
  margin-bottom:25px;min-height:52px;box-shadow:0 3px 12px rgba(25,48,66,.02);}
.topbar strong {color:#1a2a37;font-weight:760;}.topbar .sep {padding:0 11px;color:#9eb1ba;}
.topbar .right {display:flex;align-items:center;gap:13px;}.chip {display:inline-flex;gap:7px;align-items:center;
  color:#25736d;background:#e9f6f2;border-radius:6px;padding:5px 9px;font-size:11px;font-weight:700;letter-spacing:.35px;}
.live-dot {display:inline-block;width:7px;height:7px;border-radius:50%;background:#15a68b;box-shadow:0 0 0 3px #d9f4ec;}
.page-title {color:#1b2c39;font-family:"Bahnschrift","Aptos Display","Segoe UI",sans-serif;
  letter-spacing:-1.1px;font-size:31px;font-weight:750;line-height:1.12;margin:0 0 6px;}
.page-subtitle {font-size:13px;color:#708292;margin-bottom:12px;}
.kpi-card {height:124px;background:#fff;border:1px solid #e4e9ed;box-shadow:0 5px 20px rgba(22,45,61,.035);
  border-radius:11px;padding:16px 17px 14px;display:flex;flex-direction:column;justify-content:space-between;margin-top:7px;}
.kpi-top {display:flex;justify-content:space-between;align-items:center;color:#687b89;font-size:12px;font-weight:620;}
.kpi-glyph {width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;background:#e8f5f2;
  color:#0b938a;border-radius:8px;font-size:15px;font-weight:750;}
.kpi-main {display:flex;justify-content:space-between;align-items:center;gap:8px;}
.kpi-value {color:#162a3b;font-size:31px;font-weight:780;letter-spacing:-1px;line-height:1.2;}
.kpi-unit {color:#81909b;font-size:12px;margin-left:5px;}
.kpi-foot {color:#83919b;font-size:10.5px;}.kpi-foot b {color:#159b79;}
.kpi-card.orange .kpi-glyph{background:#fff0df;color:#e88a16;}
.kpi-card.orange .kpi-foot b{color:#df7d17;}
.kpi-card.red .kpi-glyph{background:#fff0ed;color:#e45b4c;}
.kpi-card.red .kpi-foot b{color:#e05749;}
.panel-h {display:flex;justify-content:space-between;align-items:center;gap:9px;margin-bottom:8px;}
.panel-heading {font-family:"Bahnschrift","Aptos Display","Segoe UI",sans-serif;font-size:16px;
  font-weight:750;color:#203340;letter-spacing:-.25px;}
.panel-detail {color:#8a98a2;font-size:11px;}
.panel-wrap {background:#fff;border:1px solid #e3e9ed;border-radius:11px; padding:15px 15px 13px;
  box-shadow:0 5px 16px rgba(18,43,57,.024);margin-top:12px;}
.panel-nopad {background:#fff;border:1px solid #e3e9ed;border-radius:11px;
  box-shadow:0 5px 16px rgba(18,43,57,.024);margin-top:12px;overflow:hidden;}
.panel-nopad .panel-h {padding:15px 16px 10px;margin:0;}
.status-pill {display:inline-block;background:#e1f5ed;color:#16876b;border-radius:5px;
  padding:3px 7px;font-size:10px;font-weight:750;letter-spacing:.25px;vertical-align:middle;margin-left:8px;}
.demo-pill {display:inline-block;background:#fff3dc;color:#9c651c;border:1px solid #f3dfbe;
  border-radius:6px;padding:5px 9px;font-size:10px;font-weight:780;letter-spacing:.7px;}
.map-caption {border-top:1px solid #e9edf0;padding:12px 15px;display:flex;align-items:center;gap:15px;
  font-size:10px;color:#647783;flex-wrap:wrap;}
.legend-line {display:inline-block;width:20px;height:4px;border-radius:2px;margin-right:5px;vertical-align:middle;}
.incident-item {margin:0 0 8px;background:#fff;border:1px solid #e9edf0;border-radius:9px;
  padding:12px 12px 10px;min-height:109px;}
.incident-item.high {border:1px solid #f8a8a1;background:linear-gradient(100deg,#fff5f3,#fff);}
.incident-top {display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
.sev {padding:4px 8px;border-radius:5px;font-size:10px;font-weight:770;}
.sev.high {background:#fde1dd;color:#c94136;}.sev.medium {background:#fff0dc;color:#af681f;}
.sev.low {background:#eaf0f4;color:#5d7583;}
.incident-title {color:#243744;font-size:13px;font-weight:720;}
.incident-road {color:#8595a0;font-size:11px;line-height:1.65;}
.incident-delta {font-size:11px;color:#d85145;font-weight:760;}
.inline-note {background:#e9f7f3;color:#26796e;border-radius:8px;font-size:11px;padding:9px 12px;line-height:1.6;}
.corridor-table {width:100%;border-collapse:collapse;font-size:11px;}
.corridor-table th {color:#7e919f;font-size:9px;letter-spacing:.8px;text-transform:uppercase;
  text-align:left;border-bottom:1px solid #e8edf0;padding:8px 8px;font-weight:770;}
.corridor-table td {border-bottom:1px solid #edf0f2;padding:9px 8px;color:#465865;}
.corridor-table tr:last-child td {border-bottom:0;}
.corridor-table .road {font-weight:730;color:#223540;}
.speed.high {color:#e65f4f;font-weight:780;}.speed.medium {color:#dc8a29;font-weight:780;}
.speed.low {color:#15937c;font-weight:780;}
.track {background:#e5eaed;border-radius:5px;height:6px;width:90px;overflow:hidden;display:inline-block;vertical-align:middle;}
.fill {display:block;height:6px;border-radius:5px;background:#1d9d80;}
.fill.high {background:#f05e50;}.fill.medium {background:#ee9a28;}
.status-bullet {width:7px;height:7px;display:inline-block;border-radius:50%;margin-right:5px;background:#1f9b7f;}
.status-bullet.high {background:#ef5549;}.status-bullet.medium {background:#ef9b32;}
.section-row {margin-top:7px;display:flex;justify-content:space-between;align-items:center;}
.section-title {font-family:"Bahnschrift","Aptos Display","Segoe UI",sans-serif;font-size:19px;font-weight:750;color:#213542;}
.muted {color:#80909c;font-size:12px;}
.eyebrow {color:#82929f;font-size:10px;letter-spacing:1.3px;text-transform:uppercase;font-weight:780;}
.empty-state {border:1px dashed #cddfe0;border-radius:11px;background:#f6faf9;text-align:center;padding:46px 22px;color:#566e76;}
.empty-state h3 {margin:7px 0;color:#203b43;font-size:17px;}
.inset-box {background:#f4f8f8;border:1px solid #e1ebeb;border-radius:10px;padding:15px;line-height:1.75;color:#536b75;font-size:12px;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#ffffff;border-color:#e3e9ed !important;border-radius:11px !important;box-shadow:0 5px 16px rgba(18,43,57,.024);}
[data-testid="stButton"] button[kind="primary"] {background:#177f7c;border:1px solid #177f7c;color:#fff;border-radius:8px;}
[data-testid="stButton"] button[kind="primary"]:hover {background:#106b69;border-color:#106b69;}
[data-testid="stButton"] button, [data-testid="stDownloadButton"] button {
  border-radius:8px;min-height:38px;font-weight:650;font-size:12px;}
[data-testid="stTabs"] button {font-size:12px;}
[data-testid="stSelectbox"] label, [data-testid="stRadio"] label, [data-testid="stTextInput"] label {font-size:12px;}
[data-testid="stAlert"] {border-radius:9px;}
.note-footer {border-top:1px solid #e1e9ed;margin-top:18px;padding-top:12px;color:#8b9ba5;font-size:10px;}
@media(max-width:1100px){.block-container{padding:1.1rem 1.3rem}.kpi-value{font-size:24px}.kpi-card{height:126px}.topbar .right{display:none}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def topbar(section: str) -> None:
    date_text = datetime.now().strftime("%a, %d %b %Y · %I:%M %p")
    st.markdown(
        f'<div class="topbar"><div>Workspace <span class="sep">›</span> '
        f'Quezon City <span class="sep">›</span> <strong>{esc(section)}</strong></div>'
        f'<div class="right"><span class="demo-pill">SAMPLE DATA</span><span>{esc(date_text)}</span></div></div>',
        unsafe_allow_html=True,
    )


def heading(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="page-title">{esc(title)}</div>'
        f'<div class="page-subtitle">{esc(subtitle)}</div>', unsafe_allow_html=True
    )


def sparkline(values: list[int], color: str) -> str:
    lo, hi = min(values), max(values)
    span = max(1, hi - lo)
    pts = " ".join(f"{i * 8:.0f},{33 - (v - lo) / span * 25:.1f}" for i, v in enumerate(values[-12:]))
    return f'<svg width="97" height="39" viewBox="0 0 97 39" aria-hidden="true"><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></svg>'


def kpi(label: str, value: str, unit: str, foot: str, values: list[int], style: str = "") -> None:
    color = "#ef6650" if style == "red" else "#e89b31" if style == "orange" else "#168f8a"
    # Fixed icon letters are deliberate typographic glyphs, not emoji.
    glyph = {"Network volume": "V", "Average speed": "S", "Congested network": "%", "Active incidents": "!"}[label]
    st.html(
        f'<div class="kpi-card {style}"><div class="kpi-top"><span>{esc(label)}</span>'
        f'<span class="kpi-glyph">{glyph}</span></div>'
        f'<div class="kpi-main"><div><span class="kpi-value">{esc(value)}</span>'
        f'<span class="kpi-unit">{esc(unit)}</span></div>{sparkline(values, color)}</div>'
        f'<div class="kpi-foot">{esc(foot)}</div></div>'
    )


def map_svg(scenario_name: str, traffic: bool) -> str:
    """Build an *illustrative* SVG schematic, not geographic or real-time map data."""
    # Transparent district blocks form a coherent, self-contained road sketch.
    blocks = []
    for r in range(6):
        for c in range(11):
            x = 30 + c * 87 + (r % 2) * 19
            y = 28 + r * 89
            fill = "#e1ebdf" if (c + r * 3) % 9 == 0 else "#e8edec" if (c + r) % 4 else "#dce8e6"
            blocks.append(f'<rect x="{x}" y="{y}" width="68" height="68" rx="3" fill="{fill}" stroke="#f8faf8" stroke-width="3"/>')
    thin_roads = []
    for x in range(-100, 1180, 91):
        thin_roads.append(f'<path d="M {x} -10 L {x+145} 600" stroke="#ffffff" stroke-width="12"/>')
    for y in range(-80, 680, 92):
        thin_roads.append(f'<path d="M -20 {y+105} L 1150 {y-65}" stroke="#ffffff" stroke-width="12"/>')
    center = '<circle cx="460" cy="415" r="61" fill="#d6e8d7" stroke="#fff" stroke-width="18"/><circle cx="460" cy="415" r="25" fill="#a8d8bc" stroke="#74b99d" stroke-width="3"/>'
    arterials = [
        ('M -20 505 C 220 445 415 342 1020 145', '#21a58a'),
        ('M -30 585 C 210 490 500 397 1095 248', '#e9ae45'),
        ('M 112 -10 C 160 175 307 340 463 600', '#26a283'),
        ('M 570 -10 C 580 180 660 350 845 610', '#20a18b'),
        ('M 0 238 C 250 210 487 175 1015 80', '#1d9a83'),
    ]
    paths = []
    for i, (d, color) in enumerate(arterials):
        paths.append(f'<path d="{d}" stroke="white" stroke-width="20" fill="none" stroke-linecap="round"/>')
        if traffic:
            actual = color
            if scenario_name == 'Rainy traffic' and i in (0, 1, 3):
                actual = '#ed9b33'
            if scenario_name == 'Vehicle collision' and i in (0, 1):
                actual = '#ec6150'
            paths.append(f'<path d="{d}" stroke="{actual}" stroke-width="7" fill="none" stroke-linecap="round" opacity=".93"/>')
        else:
            paths.append(f'<path d="{d}" stroke="#c9d8d5" stroke-width="5" fill="none" stroke-linecap="round"/>')
    incident = ""
    if scenario_name == "Vehicle collision":
        incident = '''<circle cx="662" cy="298" r="26" fill="#e95146" opacity=".17"/>
        <circle cx="662" cy="298" r="15" fill="#e95146" stroke="white" stroke-width="4"/>
        <text x="662" y="305" text-anchor="middle" font-size="19" fill="white" font-weight="bold">!</text>
        <g><rect x="688" y="248" rx="9" width="255" height="88" fill="white" stroke="#d5e2e3"/>
        <text x="703" y="273" font-size="13" fill="#263943" font-weight="bold">Possible collision</text>
        <text x="703" y="294" font-size="11" fill="#6d838f">Commonwealth Ave · DEMO</text>
        <text x="703" y="315" font-size="11" fill="#d44d43">Requires operator verification</text></g>'''
    elif scenario_name == "Rainy traffic":
        incident = '''<circle cx="532" cy="328" r="24" fill="#f3a143" opacity=".19"/>
        <circle cx="532" cy="328" r="14" fill="#e89d34" stroke="white" stroke-width="4"/>
        <text x="532" y="333" text-anchor="middle" font-size="15" fill="white" font-weight="bold">!</text>
        <rect x="560" y="287" rx="9" width="224" height="72" fill="white" stroke="#d5e2e3"/>
        <text x="576" y="311" font-size="13" fill="#263943" font-weight="bold">Wet-road advisory</text>
        <text x="576" y="334" font-size="11" fill="#788e98">Simulated conditions only</text>'''
    else:
        incident = '''<circle cx="662" cy="298" r="8" fill="#1caa91" stroke="white" stroke-width="3"/>'''
    return (
        '<svg viewBox="0 0 1010 570" xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="Illustrative schematic of Quezon City roads; not a live map" '
        'style="width:100%;height:auto;display:block;background:#f2f6f5">'
        '<rect width="1010" height="570" fill="#edf3f1"/>'
        + ''.join(blocks) + '<path d="M 790 -10 L 1040 -10 L 1040 140 Q 930 130 860 72 Z" fill="#d8eade" opacity=".88"/>'
        + ''.join(thin_roads) + center + ''.join(paths)
        + '<g fill="#7d9295" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600" letter-spacing="1">'
        '<text x="68" y="150">NORTH AVENUE</text><text x="680" y="96">UP DILIMAN</text>'
        '<text x="320" y="270">QUEZON CITY</text><text x="445" y="506" text-anchor="middle">QUEZON MEMORIAL</text>'
        '<text x="460" y="526" text-anchor="middle">CIRCLE</text><text x="700" y="492">DILIMAN</text>'
        '<text x="675" y="174" transform="rotate(-16 675 174)">COMMONWEALTH AVE</text>'
        '</g>' + incident +
        '<g><rect x="20" y="525" rx="5" width="150" height="27" fill="white" opacity=".9"/>'
        '<text x="31" y="543" font-size="11" font-family="Segoe UI,Arial" fill="#657f86">SCHEMATIC · NOT TO SCALE</text></g></svg>'
    )


def map_panel(scenario_name: str, show_traffic: bool) -> None:
    st.html(
        '<div class="panel-nopad"><div class="panel-h">'
        '<span class="panel-heading">Network conditions <span class="status-pill">DEMO VIEW</span></span>'
        '<span class="panel-detail">Quezon City · illustrative road schematic</span></div>'
        + map_svg(scenario_name, show_traffic)
        + '<div class="map-caption"><b>Legend</b>'
        '<span><i class="legend-line" style="background:#1d9d83"></i>Clear</span>'
        '<span><i class="legend-line" style="background:#e9ae45"></i>Moderate</span>'
        '<span><i class="legend-line" style="background:#ef6952"></i>Heavy</span>'
        '<span style="margin-left:auto">No live map or sensor connection</span>'
        '</div></div>'
    )


def incident_html(item: dict) -> str:
    label = 'Reviewed' if item['id'] in st.session_state.reviewed else item['time'] + ' (sample)'
    return (
        f'<div class="incident-item {esc(item["severity"])}">'
        f'<div class="incident-top"><span class="sev {esc(item["severity"])}">{esc(item["type"])}</span>'
        f'<span class="panel-detail">{esc(label)}</span></div>'
        f'<div style="display:flex;justify-content:space-between;gap:7px;align-items:center">'
        f'<span class="incident-title">{esc(item["road"])}</span><span class="incident-delta">{esc(item["delay"])}</span></div>'
        f'<div class="incident-road">{esc(item["place"])}</div>'
        '</div>'
    )


def corridor_html(rows: list[dict]) -> str:
    out = ['<table class="corridor-table"><thead><tr><th>Corridor</th><th>Speed (km/h)</th><th>Change</th><th>Congestion</th><th>Status</th></tr></thead><tbody>']
    for c in rows:
        sev = c['severity']
        out.append(
            f'<tr><td class="road">{esc(c["road"])}</td>'
            f'<td><span class="speed {sev}">{c["speed"]:.1f}</span></td>'
            f'<td>{esc(c["delta"])}</td>'
            f'<td><span class="track"><span class="fill {sev}" style="width:{c["level"]}%"></span></span></td>'
            f'<td><span class="status-bullet {sev}"></span>{esc(c["status"])}</td></tr>'
        )
    return ''.join(out) + '</tbody></table>'


def chart(scenario_name: str, compact: bool = False) -> go.Figure:
    values = SCENARIOS[scenario_name]['trend']
    baseline = [2900, 2600, 3100, 3900, 5400, 8100, 11300, 15200, 18300, 20300, 20800, 19000, 17800]
    xs = list(range(13))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=baseline, name='Typical (sample)', mode='lines',
                             line=dict(color='#bacbd1', width=2, dash='dash'), hovertemplate='%{x}:00 · %{y:,}<extra></extra>'))
    fig.add_trace(go.Scatter(x=xs, y=values, name='Selected scenario', mode='lines',
                             line=dict(color='#168f89', width=3, shape='spline'),
                             fill='tozeroy', fillcolor='rgba(22,143,137,.075)',
                             hovertemplate='%{x}:00 · %{y:,}<extra></extra>'))
    fig.update_layout(height=215 if compact else 300, margin=dict(l=0, r=5, t=8, b=0),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      showlegend=True, legend=dict(orientation='h', x=1, xanchor='right', y=1.16,
                                                  font=dict(size=10, color='#80909a')),
                      font=dict(family='Segoe UI', color='#81909d'),
                      xaxis=dict(tickmode='array', tickvals=[0, 3, 6, 9, 12],
                                 ticktext=['00:00', '03:00', '06:00', '09:00', '12:00'],
                                 showgrid=False, zeroline=False, tickfont=dict(size=10)),
                      yaxis=dict(showgrid=True, gridcolor='#edf1f3', zeroline=False,
                                 tickformat='~s', tickfont=dict(size=10)),
                      hovermode='x unified')
    return fig


def export_csv() -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['Note', 'All values are illustrative synthetic demo data, not measured traffic'])
    writer.writerow(['Scenario', st.session_state.scenario])
    writer.writerow([])
    writer.writerow(['Road', 'Speed km/h', 'Change sample', 'Congestion percent', 'Status'])
    for c in CORRIDORS:
        writer.writerow([c['road'], c['speed'], c['delta'], c['level'], c['status']])
    writer.writerow([])
    writer.writerow(['Event ID', 'Type', 'Road', 'Description', 'Severity', 'Review status'])
    for i in INCIDENTS:
        writer.writerow([i['id'], i['type'], i['road'], i['detail'], i['severity'],
                         'Reviewed' if i['id'] in st.session_state.reviewed else 'Pending'])
    return out.getvalue()


def goto(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def video_player(scenario_name: str) -> None:
    path = VIDEOS / SCENARIOS[scenario_name]['video']
    if path.is_file():
        st.video(str(path))
        st.caption(f'Playing local file: videos/{path.name}. No AI results have been generated from this video yet.')
    else:
        st.markdown(
            '<div class="empty-state"><div class="eyebrow">VIDEO SOURCE NOT FOUND</div>'
            '<h3>Place your MP4 in the videos folder</h3>'
            f'<div>Expected file: <code>videos/{esc(path.name)}</code></div></div>',
            unsafe_allow_html=True,
        )


# ---- Sidebar: navigation and workspace identity ----
with st.sidebar:
    st.markdown('''<div class="sidebar-brand"><div class="brand-row">
      <div class="brand-symbol"><span></span><span></span><span></span></div>
      <div class="brand-name">Traffic Data<br>Analytics Prototype</div></div>
      <div class="brand-sub">Operations workspace</div></div>
      <div class="sidebar-overline">Workspace</div>
      <div class="sidebar-workspace">Quezon City <span style="float:right;color:#8fb4bc">⌄</span></div>
      <div class="sidebar-overline">Monitor &amp; analytics</div>''', unsafe_allow_html=True)
    st.radio("Navigation", NAV_ITEMS, key="page", label_visibility="collapsed")
    st.markdown('''<div class="sidebar-footer"><span class="dot"></span><b>Local application</b><br>
      Interface ready · sample records<br>AI analysis not connected</div>
      <div class="side-note">NO CLOUD HOSTING REQUIRED<br>NOT A LIVE CITY TRAFFIC FEED</div>''', unsafe_allow_html=True)

page = st.session_state.page
scenario_name = st.session_state.scenario
scenario = SCENARIOS[scenario_name]
topbar(page)


if page == 'Overview':
    heading('Traffic overview', 'An interactive local prototype for reviewing sample traffic conditions and three video scenarios.')
    s1, s2, s3 = st.columns([2.7, 1.45, 1.1], vertical_alignment='bottom')
    with s1:
        st.selectbox('Focus scenario', list(SCENARIOS), key='scenario')
    with s2:
        show_traffic = st.toggle('Show schematic traffic colors', value=True)
    with s3:
        st.download_button('Export demo CSV', export_csv(), file_name='traffic_demo_data.csv', mime='text/csv', use_container_width=True)
    scenario_name = st.session_state.scenario
    scenario = SCENARIOS[scenario_name]

    k1, k2, k3, k4 = st.columns(4, gap='small')
    with k1: kpi('Network volume', f'{scenario["volume"]:,}', 'sample', '+8.2% compared to baseline (demo)', scenario['trend'])
    with k2: kpi('Average speed', f'{scenario["average_speed"]:.1f}', 'km/h', 'Illustrative, not measured', [30, 29, 28, 32, 31, 26, 25, 24, 23, 22, 21, 20], 'orange')
    with k3: kpi('Congested network', f'{scenario["congested"]:.1f}', '%', 'Illustrative road conditions', [7, 8, 6, 10, 9, 13, 12, 16, 15, 17, 17, 19], 'red')
    with k4: kpi('Active incidents', f'{scenario["incidents"]:02d}', 'focus', 'Scenario-specific demo only', [1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1], 'red')

    left, right = st.columns([2.25, 1], gap='medium')
    with left:
        view = st.radio('Monitoring view', ['Network map', 'Video feed'], horizontal=True, label_visibility='collapsed')
        if view == 'Network map':
            map_panel(scenario_name, show_traffic)
        else:
            with st.container(border=True):
                st.markdown('<div class="panel-h"><span class="panel-heading">Local video feed</span><span class="demo-pill">MP4 SOURCE</span></div>', unsafe_allow_html=True)
                video_player(scenario_name)
    with right:
        with st.container(border=True):
            st.markdown('<div class="panel-h"><span class="panel-heading">Active incidents</span><span class="panel-detail">SAMPLE LOG · 03</span></div>', unsafe_allow_html=True)
            for item in INCIDENTS:
                st.markdown(incident_html(item), unsafe_allow_html=True)
            if st.button('Investigate with local agent', use_container_width=True, type='primary'):
                goto('Local agent')

    low_left, low_right = st.columns([1.12, 1], gap='medium')
    with low_left:
        with st.container(border=True):
            st.markdown('<div class="panel-h"><span class="panel-heading">Traffic volume</span><span class="panel-detail">ILLUSTRATIVE SERIES</span></div>', unsafe_allow_html=True)
            st.plotly_chart(chart(scenario_name, compact=True), use_container_width=True, config={'displayModeBar': False})
            st.markdown('<div class="inline-note">This chart is seeded demo data. The selected scenario updates the series.</div>', unsafe_allow_html=True)
    with low_right:
        with st.container(border=True):
            st.markdown('<div class="panel-h"><span class="panel-heading">Priority corridors</span><span class="panel-detail">SAMPLE SPEEDS</span></div>', unsafe_allow_html=True)
            st.markdown(corridor_html(CORRIDORS), unsafe_allow_html=True)

elif page == 'Video sources':
    heading('Video sources', 'Select one of your three local clips and review the scene setup.')
    st.info('Video playback is real when a file is present. Weather, incident, and traffic descriptions below are demo scenario labels, not AI findings.')
    c1, c2 = st.columns([2, 1], gap='medium')
    with c1:
        st.selectbox('Video scenario', list(SCENARIOS), key='scenario')
        scenario_name = st.session_state.scenario
        scenario = SCENARIOS[scenario_name]
        with st.container(border=True):
            st.markdown('<div class="panel-h"><span class="panel-heading">Camera source preview</span><span class="demo-pill">LOCAL FILE</span></div>', unsafe_allow_html=True)
            video_player(scenario_name)
    with c2:
        with st.container(border=True):
            st.markdown('<div class="panel-heading">Scene setup</div>', unsafe_allow_html=True)
            st.markdown(f'**Scenario:** {esc(scenario_name)}')
            st.markdown(f'**Expected weather:** {esc(scenario["weather"])}')
            st.markdown(f'**Expected interpretation:** {esc(scenario["assessment"])}')
            st.markdown(f'**Proposed demo action:** {esc(scenario["recommendation"])}')
            st.markdown('<div class="inset-box">Actual YOLO detections, Qwen vision analysis, and video timestamps will be connected in a later phase.</div>', unsafe_allow_html=True)

elif page == 'Corridors':
    heading('Priority corridors', 'A filterable table of illustrative corridor metrics for layout testing.')
    query = st.text_input('Search corridors', placeholder='Search road names')
    filtered = [r for r in CORRIDORS if query.lower() in r['road'].lower()]
    with st.container(border=True):
        st.markdown('<div class="panel-h"><span class="panel-heading">Corridor status</span><span class="demo-pill">SAMPLE METRICS</span></div>', unsafe_allow_html=True)
        if filtered: st.markdown(corridor_html(filtered), unsafe_allow_html=True)
        else: st.info('No matching corridors in the sample dataset.')
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Traffic-volume illustration</div>', unsafe_allow_html=True)
        st.plotly_chart(chart(scenario_name), use_container_width=True, config={'displayModeBar': False})

elif page == 'Incidents':
    heading('Incident center', 'Review simulated event reports and test an operator acknowledgment workflow.')
    st.warning('These incident records are fictional interface examples. Acknowledgment is local to this running session and does not notify responders.')
    for item in INCIDENTS:
        c1, c2 = st.columns([4.2, 1], gap='small', vertical_alignment='center')
        with c1: st.markdown(incident_html(item), unsafe_allow_html=True)
        with c2:
            if item['id'] in st.session_state.reviewed:
                st.button('Reviewed', key='done_'+item['id'], disabled=True, use_container_width=True)
            elif st.button('Mark reviewed', key='review_'+item['id'], use_container_width=True):
                st.session_state.reviewed.add(item['id'])
                st.rerun()
    if st.button('Reset demo review states'):
        st.session_state.reviewed = set()
        st.rerun()

elif page == 'Reports':
    heading('Reports and exports', 'Export the illustrative corridor and incident records as a local CSV.')
    st.markdown('<div class="panel-wrap"><div class="panel-heading">Demo-data export</div><br><div class="inset-box">The exported CSV contains only synthetic sample metrics and sample incident logs. It does not include real detected vehicles or footage analysis.</div></div>', unsafe_allow_html=True)
    st.download_button('Download demo traffic CSV', export_csv(), file_name='traffic_data_analytics_demo.csv', mime='text/csv', type='primary')

elif page == 'Local agent':
    heading('Local agent', 'Optional Qwen-powered chat using local Ollama; no cloud endpoint required.')
    st.markdown('<div class="inset-box">This chat can reason about the explicitly labeled <b>sample scenario metadata</b> if your local Ollama server is running. It does not see frames or analyze videos yet. Qwen Code CLI and Ollama are separate installations.</div><br>', unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    question = st.chat_input('Ask about the selected scenario or demo workflow')
    if question:
        st.session_state.chat_history.append({'role': 'user', 'content': question})
        with st.chat_message('user'): st.markdown(question)
        context = json.dumps({"scenario": scenario_name, "sample_record": SCENARIOS[scenario_name]}, ensure_ascii=False)
        messages = [{"role": "system", "content": "You are the Traffic Data Analytics Prototype assistant. You have not seen the video footage. You only know the synthetic scenario metadata provided here. Explain clearly that the data is fictional and never assert that a collision occurred in real life. Do not claim to have processed frames. Keep answers concise. Sample metadata: " + context}]
        messages += st.session_state.chat_history[-10:]
        try:
            payload = json.dumps({"model": st.session_state.ollama_model, "messages": messages, "stream": False, "options": {"num_predict": 350}}).encode('utf-8')
            req = Request(LOCAL_API + '/api/chat', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
            with st.spinner('Waiting for local Ollama response…'):
                with urlopen(req, timeout=180) as response:
                    data = json.load(response)
            answer = data.get('message', {}).get('content', '').strip() or 'The local model returned an empty response.'
        except (URLError, HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            answer = ('Could not reach the local Qwen model through Ollama. Ensure Ollama is running '
                      f'and the model “{st.session_state.ollama_model}” is installed. Details: {exc}')
        st.session_state.chat_history.append({'role': 'assistant', 'content': answer})
        with st.chat_message('assistant'): st.markdown(answer)
    if st.button('Clear conversation'):
        st.session_state.chat_history = []
        st.rerun()

elif page == 'Settings':
    heading('Prototype settings', 'Local file paths and optional AI configuration.')
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Local configuration</div>', unsafe_allow_html=True)
        st.text_input('Ollama model name', key='ollama_model')
        st.code(LOCAL_API, language='text')
        st.caption('The local chat uses the Ollama HTTP API. The vision-video pipeline is not connected in this UI release.')
        if st.button('Check local Ollama server'):
            try:
                with urlopen(LOCAL_API + '/api/tags', timeout=5) as response:
                    result = json.load(response)
                names = [m.get('name', '') for m in result.get('models', [])]
                st.success('Local Ollama server reachable.')
                st.write('Installed models:', names or 'None')
            except (URLError, HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                st.error(f'Ollama not reachable on this laptop: {exc}')
    with st.container(border=True):
        st.markdown('<div class="panel-heading">Video file checklist</div>', unsafe_allow_html=True)
        for name, data in SCENARIOS.items():
            path = VIDEOS / data['video']
            st.write(f'{name}: {"File found" if path.exists() else "Missing"} — `videos/{data["video"]}`')

st.markdown('<div class="note-footer">TRAFFIC DATA ANALYTICS PROTOTYPE · LOCAL STREAMLIT APPLICATION · ALL MAPS / TRAFFIC STATISTICS / INCIDENTS SHOWN ARE SAMPLE DATA UNLESS EXPLICITLY CONNECTED TO A REAL SOURCE</div>', unsafe_allow_html=True)
