import streamlit as st
import json
import time
import threading
import queue
from pathlib import Path
from dataclasses import asdict

# Page config must be the first Streamlit call
st.set_page_config(
    page_title="AMCACI | Video Intelligence Pipeline",
    page_icon="🅰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Global CSS - dark professional theme
# ---------------------------------------------------------------------------

GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #ffffff;
    }

    .stApp {
        background-color: #000000;
    }

    /* Remove top padding Streamlit adds */
    .stAppHeader { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    .block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #09090b;
        border-right: 1px solid #27272a; /* zinc-800 */
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {
        color: #a1a1aa; /* zinc-400 */
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
    }

    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.03em;
    }

    /* Primary Action Buttons */
    .stButton > button {
        background-color: #ffffff;
        color: #09090b;
        border: none;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.5rem 1.25rem;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }

    .stButton > button:hover {
        background-color: #f4f4f5;
        transform: translateY(-1px);
    }

    .stButton > button:disabled {
        background-color: #27272a;
        color: #71717a;
        cursor: not-allowed;
    }

    /* Download button (Prefect secondary style) */
    .stDownloadButton > button {
        background-color: transparent;
        color: #d4d4d8;
        border: 1px solid #3f3f46;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.35rem 0.9rem;
        transition: all 0.2s ease;
    }

    .stDownloadButton > button:hover {
        background-color: #27272a;
        color: #ffffff;
        border-color: #52525b;
    }

    /* Input fields */
    .stTextInput > div > input,
    .stTextArea > div > textarea {
        background-color: #121214;
        color: #ffffff;
        border: 1px solid #27272a;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
    }

    .stTextInput > div > input:focus,
    .stTextArea > div > textarea:focus {
        border-color: #e4e4e7;
        box-shadow: 0 0 0 1px #e4e4e7;
    }

    /* Sliders */
    .stSlider > div > div > div > div {
        background-color: #ffffff;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #121214;
        border: 1px solid #27272a;
        color: #ffffff;
        border-radius: 6px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #121214;
        border: 1px solid #27272a;
        border-radius: 8px;
        color: #a1a1aa;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .streamlit-expanderContent {
        background-color: #09090b;
        border: 1px solid #27272a;
        border-top: none;
        border-radius: 0 0 8px 8px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #121214;
        border: 1px solid #27272a;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }

    [data-testid="stMetricLabel"] {
        color: #a1a1aa;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Code blocks */
    code, pre {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        background-color: #121214;
        color: #a1a1aa;
        border: 1px solid #27272a;
    }

    /* Dividers */
    hr {
        border-color: #27272a;
        margin: 1.5rem 0;
    }

    /* File uploader */
    .stFileUploader > div {
        background-color: #121214;
        border: 1px dashed #52525b;
        border-radius: 8px;
    }

    .stFileUploader label {
        color: #a1a1aa;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #ffffff;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid #27272a;
        gap: 0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #71717a;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.6rem 1.25rem;
        border-bottom: 2px solid transparent;
    }

    .stTabs [aria-selected="true"] {
        color: #ffffff;
        border-bottom: 2px solid #ffffff;
        background-color: transparent;
    }

    /* Audio player */
    audio {
        width: 100%;
        border-radius: 6px;
        filter: invert(0.9) hue-rotate(180deg);
    }

    /* JSON viewer */
    .stJson {
        background-color: #121214;
        border: 1px solid #27272a;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid #27272a;
        border-radius: 6px;
    }

    /* Status container override */
    [data-testid="stStatusWidget"] {
        background-color: #121214;
        border: 1px solid #27272a;
        border-radius: 8px;
    }

    /* Notification / toast */
    .stAlert {
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        background-color: #121214;
        border: 1px solid #27272a;
        color: #ffffff;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #1c1c1c;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {
        color: #a1a1aa;
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
    }

    /* Headings */
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.03em;
    }

    /* Primary Action Buttons - Render style white */
    .stButton > button {
        background-color: #ffffff;
        color: #000000;
        border: none;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.5rem 1.25rem;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }

    .stButton > button:hover {
        background-color: #e4e4e7;
        transform: translateY(-1px);
    }

    .stButton > button:disabled {
        background-color: #1c1c1c;
        color: #52525b;
        cursor: not-allowed;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: transparent;
        color: #d4d4d8;
        border: 1px solid #3f3f46;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.35rem 0.9rem;
        transition: all 0.2s ease;
    }

    .stDownloadButton > button:hover {
        background-color: #1c1c1c;
        color: #ffffff;
        border-color: #52525b;
    }

    /* Input fields */
    .stTextInput > div > input,
    .stTextArea > div > textarea {
        background-color: #111111;
        color: #ffffff;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
    }

    .stTextInput > div > input:focus,
    .stTextArea > div > textarea:focus {
        border-color: #7c3aed;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2);
    }

    /* Sliders */
    .stSlider > div > div > div > div {
        background-color: #7c3aed;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background-color: #111111;
        border: 1px solid #2a2a2a;
        color: #ffffff;
        border-radius: 6px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #111111;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        color: #a1a1aa;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .streamlit-expanderContent {
        background-color: #000000;
        border: 1px solid #2a2a2a;
        border-top: none;
        border-radius: 0 0 8px 8px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #111111;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }

    [data-testid="stMetricLabel"] {
        color: #a1a1aa;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Code blocks */
    code, pre {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        background-color: #111111;
        color: #a1a1aa;
        border: 1px solid #2a2a2a;
    }

    /* Dividers */
    hr {
        border-color: #1c1c1c;
        margin: 1.5rem 0;
    }

    /* File uploader */
    .stFileUploader > div {
        background-color: #111111;
        border: 2px dashed #3a1a6e;
        border-radius: 12px;
    }

    .stFileUploader label { color: #a1a1aa; }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #7c3aed, #6d28d9);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid #1c1c1c;
        gap: 0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #52525b;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.6rem 1.25rem;
        border-bottom: 2px solid transparent;
    }

    .stTabs [aria-selected="true"] {
        color: #ffffff;
        border-bottom: 2px solid #7c3aed;
        background-color: transparent;
    }

    /* Audio player */
    audio {
        width: 100%;
        border-radius: 6px;
        filter: invert(0.9) hue-rotate(180deg);
    }

    /* JSON viewer */
    .stJson {
        background-color: #111111;
        border: 1px solid #2a2a2a;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid #2a2a2a;
        border-radius: 6px;
    }

    [data-testid="stStatusWidget"] {
        background-color: #111111;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
    }

    .stAlert {
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        background-color: #111111;
        border: 1px solid #2a2a2a;
        color: #ffffff;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #000000; }
    ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SVG icon definitions
# ---------------------------------------------------------------------------

def svg_icon(icon_name: str, size: int = 16, color: str = "#60a5fa") -> str:
    icons = {
        "upload": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>""",
        "play": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>""",
        "check": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
        "loader": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>""",
        "warning": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>""",
        "download": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>""",
        "mic": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>""",
        "cluster": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>""",
        "agent": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>""",
        "text": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
        "speaker": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>""",
        "refresh": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>""",
        "settings": f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>""",
    }
    return icons.get(icon_name, "")


def icon_label(icon_name: str, label: str, size: int = 15, color: str = "#60a5fa") -> str:
    return f"""
    <div style="display:flex;align-items:center;gap:8px;margin:0;">
        {svg_icon(icon_name, size, color)}
        <span style="font-size:0.875rem;font-weight:500;color:#d4d4d8;">{label}</span>
    </div>
    """


# ---------------------------------------------------------------------------
# Component renderers
# ---------------------------------------------------------------------------

def render_topnav(show_launch_btn: bool = True):
    """Slim sticky top navigation bar shown on the app page."""
    st.markdown("""
    <div style="
        position: sticky;
        top: 0;
        z-index: 999;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid #1c1c1c;
        padding: 0 2.5rem;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    ">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="
                width: 40px; height: 40px;
                background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 60%, #06b6d4 100%);
                border-radius: 10px;
                display:flex;align-items:center;justify-content:center;
                flex-shrink:0;
                box-shadow: 0 0 16px rgba(124,58,237,0.45);
            ">
                <svg width="22" height="22" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M50 10 L85 80 L72 80 L62 58 L38 58 L28 80 L15 80 Z" fill="white"/>
                    <path d="M50 30 L66 58 L34 58 Z" fill="url(#ag)" opacity="0.5"/>
                    <defs>
                        <linearGradient id="ag" x1="34" y1="58" x2="66" y2="30" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#a78bfa"/>
                            <stop offset="1" stop-color="#06b6d4"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <span style="font-size:1.1rem;font-weight:800;color:#ffffff;letter-spacing:-0.03em;">AMCACI</span>
        </div>
        <div style="display:flex;align-items:center;gap:2rem;">
            <span style="font-size:0.82rem;color:#52525b;font-weight:500;">Pipeline</span>
            <span style="font-size:0.82rem;color:#52525b;font-weight:500;">Results</span>
            <span style="font-size:0.82rem;color:#52525b;font-weight:500;">Docs</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_landing_page():
    """Full-page landing experience inspired by Prefect.io and Render.com"""

    # ── Top Nav ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: rgba(0,0,0,0.9);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid #1a1a1a;
        padding: 0 3rem;
        height: 68px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0;
    ">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="
                width: 46px; height: 46px;
                background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 60%, #06b6d4 100%);
                border-radius: 12px;
                display:flex;align-items:center;justify-content:center;
                flex-shrink:0;
                box-shadow: 0 0 24px rgba(124,58,237,0.5);
            ">
                <svg width="26" height="26" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M50 10 L85 80 L72 80 L62 58 L38 58 L28 80 L15 80 Z" fill="white"/>
                    <path d="M50 30 L66 58 L34 58 Z" fill="url(#ag2)" opacity="0.55"/>
                    <defs>
                        <linearGradient id="ag2" x1="34" y1="58" x2="66" y2="30" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#a78bfa"/>
                            <stop offset="1" stop-color="#06b6d4"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <span style="font-size:1.25rem;font-weight:800;color:#ffffff;letter-spacing:-0.03em;">AMCACI</span>
        </div>
        <div style="display:flex;align-items:center;gap:2.5rem;">
            <span style="font-size:0.85rem;color:#71717a;font-weight:500;">Pipeline</span>
            <span style="font-size:0.85rem;color:#71717a;font-weight:500;">Research</span>
            <span style="font-size:0.85rem;color:#71717a;font-weight:500;">Architecture</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hero Section ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        min-height: 88vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 6rem 3rem 4rem 3rem;
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(ellipse 80% 60% at 70% 30%, rgba(109, 40, 217, 0.25) 0%, transparent 60%),
            radial-gradient(ellipse 60% 50% at 80% 70%, rgba(14, 165, 233, 0.15) 0%, transparent 55%),
            radial-gradient(ellipse 50% 60% at 20% 50%, rgba(124, 58, 237, 0.1) 0%, transparent 60%),
            #000000;
    ">
        <div style="max-width: 780px; position: relative; z-index: 1;">
            <div style="margin-bottom: 2rem;">
                <span style="
                    background: rgba(124, 58, 237, 0.15);
                    border: 1px solid rgba(124, 58, 237, 0.4);
                    color: #a78bfa;
                    font-size: 0.78rem;
                    padding: 5px 14px;
                    border-radius: 999px;
                    font-weight: 600;
                    letter-spacing: 0.06em;
                    text-transform: uppercase;
                    font-family: Inter, sans-serif;
                ">Capstone &mdash; AI_DS_024</span>
            </div>
            <h1 style="
                margin: 0 0 1.5rem 0;
                font-size: clamp(2.8rem, 5vw, 4.5rem);
                font-weight: 700;
                color: #ffffff;
                letter-spacing: -0.04em;
                line-height: 1.05;
                font-family: Inter, sans-serif;
            ">Your fastest path to<br>
            <span style="
                background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 40%, #06b6d4 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">multi-modal intelligence.</span>
            </h1>
            <p style="
                margin: 0 0 3rem 0;
                font-size: 1.15rem;
                color: #71717a;
                font-weight: 400;
                line-height: 1.65;
                font-family: Inter, sans-serif;
                max-width: 580px;
            ">
                Upload any news broadcast. AMCACI autonomously extracts audio, transcribes,
                clusters topics with AI agents, and synthesizes personalized summaries &mdash; end-to-end.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Launch Button ─────────────────────────────────────────────────────────
    col_btn, col_ghost, _ = st.columns([1.2, 1.3, 4])
    with col_btn:
        if st.button("Launch Pipeline  →", key="btn_launch", use_container_width=True):
            st.session_state.current_page = "app"
            st.rerun()
    with col_ghost:
        st.markdown("""
        <div style="
            display:flex;align-items:center;gap:8px;
            padding:0.5rem 0;
            cursor:pointer;
        ">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#71717a"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polygon points="10 8 16 12 10 16 10 8"/>
            </svg>
            <span style="font-size:0.88rem;color:#71717a;font-weight:500;">View Architecture</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Feature Cards Section ─────────────────────────────────────────────────
    st.markdown("""
    <div style="
        padding: 5rem 3rem 2rem 3rem;
        border-top: 1px solid #111111;
        margin-top: 0;
    ">
        <p style="
            font-size:0.7rem;font-weight:600;color:#52525b;
            text-transform:uppercase;letter-spacing:0.12em;
            margin:0 0 0.75rem 0;
        ">Core Pipeline</p>
        <h2 style="
            font-size:2.5rem;font-weight:700;color:#ffffff;
            letter-spacing:-0.03em;line-height:1.15;
            margin:0 0 1rem 0;
        ">Autonomous intelligence,<br>
        <span style="color:#7c3aed;">zero manual steps.</span></h2>
        <p style="font-size:1rem;color:#52525b;margin:0 0 3rem 0;max-width:540px;line-height:1.6;">
            From raw video to structured summaries — every stage is orchestrated by the pipeline.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature grid
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    features = [
        (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>',
            "Audio Intelligence",
            "Silero VAD, noisereduce, and Whisper medium deliver punctuated transcripts with word-level timestamps."
        ),
        (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
            "Semantic Clustering",
            "SBERT embeddings + sliding-window zero-shot BART classify sentences into topic groups, refined by HDBSCAN sub-clustering."
        ),
        (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>',
            "Agentic Evaluation",
            "Llama-3.3-70b Agent 1 diagnoses clustering metrics, tunes HDBSCAN parameters, and relabels topics autonomously."
        ),
        (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
            "Multi-Depth Summarization",
            "Extractive SBERT + abstractive BART-large-cnn, upgraded by Agent 2 when ROUGE-L drops below threshold."
        ),
        (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ec4899" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
            "Text to Speech",
            "Coqui TTS (tacotron2-DDC) synthesizes natural-sounding audio summaries for each topic category."
        ),
        (
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>',
            "Visual Pipeline",
            "Timestamps align topics to video segments; CLIP embeddings drive keyframe extraction with diversity guarantees."
        ),
    ]
    for col, (icon, title, desc) in zip([feat_col1, feat_col2, feat_col3, feat_col1, feat_col2, feat_col3], features):
        with col:
            st.markdown(f"""
            <div style="
                background: #0a0a0a;
                border: 1px solid #1c1c1c;
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                transition: border-color 0.2s;
            ">
                <div style="margin-bottom:1rem;">{icon}</div>
                <h4 style="margin:0 0 0.5rem 0;font-size:0.95rem;font-weight:600;color:#ffffff;letter-spacing:-0.01em;">{title}</h4>
                <p style="margin:0;font-size:0.82rem;color:#52525b;line-height:1.65;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Tech Stack Section ────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        padding: 4rem 3rem;
        background: linear-gradient(180deg, #000000 0%, #070014 50%, #000000 100%);
        margin-top: 2rem;
        border-top: 1px solid #111111;
        border-bottom: 1px solid #111111;
    ">
        <p style="
            text-align:center;font-size:0.7rem;font-weight:600;
            color:#3f3f46;text-transform:uppercase;letter-spacing:0.12em;
            margin:0 0 2.5rem 0;
        ">Powered by</p>
        <div style="display:flex;flex-wrap:wrap;gap:0.75rem;justify-content:center;align-items:center;">
    """, unsafe_allow_html=True)

    tech_stack = [
        ("Whisper", "#7c3aed"), ("SBERT", "#4f46e5"), ("HDBSCAN", "#0284c7"),
        ("BART-MNLI", "#0891b2"), ("BART-CNN", "#059669"), ("Llama 3.3", "#7c3aed"),
        ("Groq", "#d97706"), ("Coqui TTS", "#dc2626"), ("Silero VAD", "#7c3aed"),
        ("CLIP", "#4f46e5"), ("UMAP", "#0284c7"), ("Plotly", "#9333ea"),
    ]
    badges_html = "".join([
        f'<span style="'
        f'background:rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.15);'
        f'border:1px solid rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.4);'
        f'color:{c};font-size:0.8rem;font-weight:600;padding:6px 16px;'
        f'border-radius:999px;font-family:Inter,sans-serif;letter-spacing:0.01em;'
        f'">{name}</span>'
        for name, c in tech_stack
    ])
    st.markdown(f"""
        <div style="display:flex;flex-wrap:wrap;gap:0.75rem;justify-content:center;padding:0 3rem;">
            {badges_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Final CTA ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        padding: 5rem 3rem;
        text-align: center;
        background: radial-gradient(ellipse 70% 60% at 50% 50%, rgba(109, 40, 217, 0.2) 0%, transparent 70%);
    ">
        <h2 style="
            font-size:2.2rem;font-weight:700;color:#ffffff;
            letter-spacing:-0.03em;margin:0 0 1rem 0;
        ">Ready to analyse your broadcast?</h2>
        <p style="color:#52525b;font-size:1rem;margin:0 auto 2.5rem auto;max-width:480px;line-height:1.6;">
            Upload your video and let the pipeline do the rest.
            Transcription, clustering, and summarization — automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([2, 1.5, 2])
    with col_c:
        if st.button("Get Started  →", key="btn_launch_cta", use_container_width=True):
            st.session_state.current_page = "app"
            st.rerun()

    st.markdown("""
    <div style="
        border-top:1px solid #111111;padding:2rem 3rem;
        display:flex;align-items:center;justify-content:space-between;
    ">
        <span style="font-size:0.78rem;color:#27272a;">© 2025 AMCACI — Shiv Nadar University Chennai</span>
        <span style="font-size:0.78rem;color:#27272a;">AI_DS_024</span>
    </div>
    """, unsafe_allow_html=True)


def render_app_header():
    """Compact header shown at the top of the app page."""
    render_topnav(show_launch_btn=False)
    st.markdown("""
    <div style="
        padding: 3rem 3rem 2rem 3rem;
        background:
            radial-gradient(ellipse 60% 80% at 80% 20%, rgba(109, 40, 217, 0.2) 0%, transparent 60%),
            radial-gradient(ellipse 50% 60% at 10% 80%, rgba(14, 165, 233, 0.1) 0%, transparent 60%),
            #000000;
        border-bottom: 1px solid #111111;
        margin-bottom: 2rem;
    ">
        <div style="max-width: 700px;">
            <div style="margin-bottom:1.25rem;">
                <span style="
                    background:rgba(124,58,237,0.15);
                    border:1px solid rgba(124,58,237,0.4);
                    color:#a78bfa;
                    font-size:0.72rem;font-weight:600;
                    padding:4px 12px;border-radius:999px;
                    letter-spacing:0.07em;text-transform:uppercase;
                ">Pipeline Active</span>
            </div>
            <h1 style="
                margin:0 0 0.75rem 0;
                font-size:2.5rem;font-weight:700;
                color:#ffffff;letter-spacing:-0.04em;line-height:1.1;
            ">Content Analysis<br>
            <span style="
                background:linear-gradient(135deg,#a78bfa,#7c3aed,#06b6d4);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            ">Pipeline</span>
            </h1>
            <p style="margin:0;font-size:0.95rem;color:#52525b;line-height:1.5;">
                Upload a news broadcast video. The pipeline will extract, transcribe, cluster, and summarise automatically.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stage_header(icon: str, stage_number: int, title: str, status: str = "pending"):
    status_colors = {
        "pending": "#27272a",
        "running": "#ffffff",
        "complete": "#10b981",
        "failed": "#ef4444",
    }
    status_labels = {
        "pending": "Pending",
        "running": "In Progress",
        "complete": "Complete",
        "failed": "Failed",
    }
    color = status_colors.get(status, "#27272a")
    label = status_labels.get(status, "Pending")

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background-color: #121214;
        border: 1px solid #27272a;
        border-left: 3px solid {color};
        border-radius: 6px;
        margin-bottom: 0.5rem;
    ">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="
                font-size:0.7rem;
                font-weight:600;
                color:#a1a1aa;
                font-family:'JetBrains Mono',monospace;
                background:#09090b;
                padding:2px 7px;
                border-radius:4px;
                border:1px solid #27272a;
            ">STAGE {stage_number:02d}</span>
            {svg_icon(icon, 15, color)}
            <span style="font-size:0.875rem;font-weight:600;color:#d4d4d8;">{title}</span>
        </div>
        <span style="
            font-size:0.7rem;
            font-weight:500;
            color:{color};
            letter-spacing:0.05em;
            text-transform:uppercase;
        ">{label}</span>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, status: str = "neutral", delta_text: str = ""):
    status_colors = {
        "good": "#10b981",
        "warn": "#d97706",
        "bad": "#ef4444",
        "neutral": "#3b82f6",
    }
    color = status_colors.get(status, "#3b82f6")

    st.markdown(f"""
    <div style="
        background-color: #121214;
        border: 1px solid #27272a;
        border-top: 2px solid {color};
        border-radius: 8px;
        padding: 1rem 1.1rem;
        height: 100%;
    ">
        <p style="
            margin:0 0 0.35rem 0;
            font-size:0.7rem;
            font-weight:600;
            color:#a1a1aa;
            text-transform:uppercase;
            letter-spacing:0.07em;
        ">{label}</p>
        <p style="
            margin:0;
            font-size:1.5rem;
            font-weight:700;
            color:#ffffff;
            font-family:'JetBrains Mono',monospace;
            line-height:1.2;
        ">{value}</p>
        {f'<p style="margin:0.3rem 0 0 0;font-size:0.72rem;color:{color};font-weight:500;">{delta_text}</p>' if delta_text else ''}
    </div>
    """, unsafe_allow_html=True)


def render_log_entry(message: str, level: str = "info"):
    colors = {
        "info": "#3b82f6",
        "success": "#10b981",
        "warn": "#f59e0b",
        "error": "#ef4444",
    }
    prefixes = {
        "info": "INFO ",
        "success": "DONE ",
        "warn": "WARN ",
        "error": "ERR  ",
    }
    color = colors.get(level, "#3b82f6")
    prefix = prefixes.get(level, "INFO ")
    ts = time.strftime("%H:%M:%S")

    st.markdown(f"""
    <div style="
        display:flex;
        align-items:flex-start;
        gap:10px;
        padding:0.3rem 0;
        border-bottom:1px solid #09090b;
        font-family:'JetBrains Mono',monospace;
        font-size:0.78rem;
    ">
        <span style="color:#27272a;white-space:nowrap;">{ts}</span>
        <span style="color:{color};font-weight:600;white-space:nowrap;">{prefix}</span>
        <span style="color:#94a3b8;">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_cluster_card(cluster: dict, index: int):
    confidence_pct = int(cluster.get("confidence", 0) * 100)
    num_sentences = len(cluster.get("sentences", []))
    category = cluster.get("category", "Unknown")

    st.markdown(f"""
    <div style="
        background-color: #121214;
        border: 1px solid #27272a;
        border-radius: 8px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.6rem;
    ">
        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:0.6rem;
        ">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="
                    font-size:0.68rem;
                    font-weight:600;
                    color:#a1a1aa;
                    font-family:'JetBrains Mono',monospace;
                    background:#09090b;
                    padding:2px 7px;
                    border-radius:4px;
                    border:1px solid #27272a;
                ">C-{index:02d}</span>
                <span style="
                    font-size:0.875rem;
                    font-weight:600;
                    color:#ffffff;
                ">{category}</span>
            </div>
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:0.75rem;color:#71717a;">{num_sentences} segments</span>
                <span style="
                    font-size:0.75rem;
                    font-weight:600;
                    color:{'#10b981' if confidence_pct >= 70 else '#f59e0b' if confidence_pct >= 50 else '#ef4444'};
                    font-family:'JetBrains Mono',monospace;
                ">{confidence_pct}%</span>
            </div>
        </div>
        <div style="
            background-color:#09090b;
            border-radius:6px;
            padding:0.65rem 0.85rem;
            font-size:0.8rem;
            color:#71717a;
            line-height:1.5;
            font-style:italic;
        ">
            "{cluster['sentences'][0] if cluster.get('sentences') else 'No sentences'}"
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_summary_card(summary: dict, tts_path: str = None, video_result: dict = None, idx: int = 0):
    category = summary.get("category", "Unknown")
    text = summary.get("abstractive_summary", "")
    rouge = summary.get("rouge_scores", {})
    agent_refined = summary.get("agent_refined", False)
    r1 = rouge.get("rouge1", 0)
    rl = rouge.get("rougeL", 0)

    badge_color = "#27272a" if not agent_refined else "#7c3aed"
    badge_text_color = "#ffffff" if not agent_refined else "#ffffff"
    badge_text = "BART" if not agent_refined else "LLM Agent"

    st.markdown(f"""
    <div style="
        background-color: #121214;
        border: 1px solid #27272a;
        border-radius: 8px;
        padding: 1.15rem 1.25rem 0.85rem 1.25rem;
        margin-bottom: 0.75rem;
    ">
        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:0.75rem;
        ">
            <span style="font-size:0.95rem;font-weight:600;color:#ffffff;">{category}</span>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="
                    font-size:0.65rem;
                    font-weight:600;
                    color:{badge_text_color};
                    background:{badge_color};
                    padding:2px 8px;
                    border-radius:4px;
                    letter-spacing:0.04em;
                ">{badge_text}</span>
                <span style="
                    font-size:0.72rem;
                    color:#71717a;
                    font-family:'JetBrains Mono',monospace;
                ">R1:{r1:.2f} RL:{rl:.2f}</span>
            </div>
        </div>
        <p style="
            margin:0;
            font-size:0.85rem;
            color:#a1a1aa;
            line-height:1.65;
        ">{text}</p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([3, 1.2, 1.2])
    with col_b:
        st.download_button(
            label="Export TXT",
            data=text,
            file_name=f"{category.replace(' ', '_').lower()}_summary.txt",
            mime="text/plain",
            key=f"dl_txt_{category}_{idx}",
        )
    with col_c:
        summary_json = json.dumps(summary, indent=2)
        st.download_button(
            label="Export JSON",
            data=summary_json,
            file_name=f"{category.replace(' ', '_').lower()}_summary.json",
            mime="application/json",
            key=f"dl_json_{category}_{idx}",
        )

    if tts_path and Path(tts_path).exists():
        with open(tts_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/wav")
        st.download_button(
            label="Download Audio",
            data=audio_bytes,
            file_name=f"{category.replace(' ', '_').lower()}_audio.wav",
            mime="audio/wav",
            key=f"dl_wav_{category}_{idx}",
        )

    if video_result:
        video_path = video_result.get("summary_video_path")
        keyframes = video_result.get("keyframes", [])
        
        if video_path and Path(video_path).exists():
            st.markdown(f"""
            <div style="font-size:0.875rem;font-weight:600;color:#ffffff;margin:1rem 0 0.5rem 0;">
                Compiled Video Summary
            </div>
            """, unsafe_allow_html=True)
            st.video(video_path)
            
            with open(video_path, "rb") as file:
                st.download_button(
                    label="Download Video Demo",
                    data=file,
                    file_name=Path(video_path).name,
                    mime="video/mp4",
                    key=f"dl_vid_{category}_{idx}"
                )
        
        if keyframes:
            with st.expander("Extracted Keyframes (3 per sentence)"):
                import itertools
                for text_str, group in itertools.groupby(keyframes, key=lambda x: x.get("text")):
                    group_list = list(group)
                    st.markdown(f"<p style='font-size:0.8rem; margin:0.5rem 0 0.2rem 0; color:#a1a1aa;'>{text_str}</p>", unsafe_allow_html=True)
                    cols = st.columns(3)
                    for frame_info, col in zip(group_list, cols):
                        fp = frame_info.get("frame_path")
                        if fp and Path(fp).exists():
                            label = f"{frame_info.get('frame_type', '')} ({frame_info.get('timestamp', 0):.2f}s)"
                            col.image(fp, caption=label)


def render_agent_diagnosis(instructions: dict, attempt: int):
    action = instructions.get("suggested_action", "N/A")
    diagnosis = instructions.get("diagnosis", "")
    rationale = instructions.get("rationale", "")
    merge_pairs = instructions.get("merge_pairs") or []
    relabels = instructions.get("relabel_suggestions") or {}
    new_mcs = instructions.get("new_min_cluster_size")
    new_ms = instructions.get("new_min_samples")

    st.markdown(f"""
    <div style="
        background-color: #0f172a;
        border: 1px solid #1e3a5f;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem 1.15rem;
        margin: 0.5rem 0;
    ">
        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:0.6rem;
        ">
            <span style="
                font-size:0.75rem;
                font-weight:600;
                color:#60a5fa;
                text-transform:uppercase;
                letter-spacing:0.06em;
            ">Agent 1 — Attempt {attempt} Diagnosis</span>
            <span style="
                font-size:0.7rem;
                font-weight:600;
                color:#ffffff;
                background:#ffffff;
                padding:2px 8px;
                border-radius:4px;
            ">{action.replace('_', ' ').upper()}</span>
        </div>
        <p style="margin:0 0 0.5rem 0;font-size:0.82rem;color:#94a3b8;line-height:1.55;">{diagnosis}</p>
        {f'<p style="margin:0;font-size:0.78rem;color:#71717a;font-style:italic;">{rationale}</p>' if rationale else ''}
    </div>
    """, unsafe_allow_html=True)

    if merge_pairs:
        merges = ", ".join(f"{a} + {b}" for a, b in merge_pairs)
        st.markdown(f"""
        <div style="
            background:#121214;border:1px solid #27272a;border-radius:6px;
            padding:0.5rem 0.85rem;margin-top:0.4rem;font-size:0.78rem;color:#94a3b8;
        ">
            <strong style="color:#d4d4d8;">Merge Pairs:</strong> {merges}
        </div>
        """, unsafe_allow_html=True)

    if relabels:
        relabel_str = " | ".join(f"{k} -> {v}" for k, v in relabels.items())
        st.markdown(f"""
        <div style="
            background:#121214;border:1px solid #27272a;border-radius:6px;
            padding:0.5rem 0.85rem;margin-top:0.4rem;font-size:0.78rem;color:#94a3b8;
        ">
            <strong style="color:#d4d4d8;">Relabels:</strong> {relabel_str}
        </div>
        """, unsafe_allow_html=True)

    if new_mcs or new_ms:
        params = []
        if new_mcs:
            params.append(f"min_cluster_size = {new_mcs}")
        if new_ms:
            params.append(f"min_samples = {new_ms}")
        st.markdown(f"""
        <div style="
            background:#121214;border:1px solid #27272a;border-radius:6px;
            padding:0.5rem 0.85rem;margin-top:0.4rem;font-size:0.78rem;
            color:#94a3b8;font-family:'JetBrains Mono',monospace;
        ">
            <strong style="color:#d4d4d8;">Parameter Adjustments:</strong> {" | ".join(params)}
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "current_page": "landing",  # 'landing' or 'app'
        "pipeline_running": False,
        "pipeline_complete": False,
        "run_id": None,
        "transcript": None,
        "clusters": None,
        "metrics": None,
        "summaries": None,
        "tts_paths": None,
        "video_results": {},
        "stage_statuses": {
            "audio_extraction": "pending",
            "preprocessing": "pending",
            "transcription": "pending",
            "clustering": "pending",
            "agent1_eval": "pending",
            "summarization": "pending",
            "tts": "pending",
            "video_processing": "pending",
        },
        "log_messages": [],
        "agent1_events": [],
        "feedback_submitted": False,
        "feedback_prefs": {},
        "event_queue": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def push_log(message: str, level: str = "info"):
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    st.session_state.log_messages.append({"message": message, "level": level, "ts": time.time()})


def set_stage_status(stage: str, status: str):
    st.session_state.stage_statuses[stage] = status
    # Update the sidebar status display if placeholder exists
    if hasattr(st.session_state, 'sidebar_status_placeholder') and st.session_state.sidebar_status_placeholder:
        try:
            st.session_state.sidebar_status_placeholder.markdown(render_sidebar_status(), unsafe_allow_html=True)
        except:
            pass  # Ignore if placeholder is not available
    time.sleep(0.1)  # Small delay to ensure state is saved


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar_status():
    """Render just the status indicators part of the sidebar"""
    stages = [
        ("upload",   "Video Upload",              None),
        ("mic",      "Audio Extraction",           "audio_extraction"),
        ("loader",   "Voice Preprocessing",        "preprocessing"),
        ("text",     "Transcription",              "transcription"),
        ("cluster",  "Embedding & Clustering",     "clustering"),
        ("agent",    "Agent 1 — Evaluation",       "agent1_eval"),
        ("text",     "Summarization",              "summarization"),
        ("agent",    "Agent 2 — Refinement",       "summarization"),
        ("speaker",  "Text to Speech",             "tts"),
        ("video",    "Video Compilation",          "video_processing"),
    ]

    status_html = ""
    for icon, label, key in stages:
        if key is None:
            status = "complete" if st.session_state.get("run_id") else "pending"
        else:
            status = st.session_state.stage_statuses.get(key, "pending")

        # Status colors and icons
        if status == "pending":
            status_color = "#27272a"
            status_icon = "○"
            bg_color = "transparent"
            text_color = "#71717a"
            text_weight = "400"
            glow_style = ""
        elif status == "running":
            status_color = "#f59e0b"
            status_icon = "◐"
            bg_color = "rgba(245, 158, 11, 0.1)"
            text_color = "#f59e0b"
            text_weight = "600"
            glow_style = "box-shadow: 0 0 8px rgba(245, 158, 11, 0.6);"
        elif status == "complete":
            status_color = "#10b981"
            status_icon = "✓"
            bg_color = "transparent"
            text_color = "#d4d4d8"
            text_weight = "500"
            glow_style = ""
        else:  # failed
            status_color = "#ef4444"
            status_icon = "✗"
            bg_color = "transparent"
            text_color = "#ef4444"
            text_weight = "500"
            glow_style = ""

        status_html += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:0.5rem 0.6rem;border-radius:6px;background:{bg_color};margin-bottom:4px;transition:all 0.3s ease;">
            <div style="width:20px;height:20px;border-radius:50%;background-color:{status_color};display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:0.7rem;color:#ffffff;font-weight:700;{glow_style}transition:all 0.3s ease;">{status_icon}</div>
            <span style="font-size:0.78rem;color:{text_color};font-weight:{text_weight};line-height:1.3;flex:1;">{label}</span>
        </div>
        """
    
    return status_html


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.25rem 0 1rem 0;border-bottom:1px solid #27272a;margin-bottom:1rem;">
            <p style="margin:0;font-size:0.65rem;font-weight:600;color:#27272a;text-transform:uppercase;
                      letter-spacing:0.1em;">Pipeline Status</p>
        </div>
        """, unsafe_allow_html=True)

        # Create a placeholder for dynamic status updates
        status_placeholder = st.empty()
        status_placeholder.markdown(render_sidebar_status(), unsafe_allow_html=True)
        
        # Store the placeholder in session state so we can update it
        st.session_state.sidebar_status_placeholder = status_placeholder

        st.markdown("<hr style='border-color:#27272a;margin:1rem 0;'>", unsafe_allow_html=True)

        st.markdown("""
        <p style="margin:0 0 0.75rem 0;font-size:0.65rem;font-weight:600;color:#27272a;
                  text-transform:uppercase;letter-spacing:0.1em;">Configuration</p>
        """, unsafe_allow_html=True)

        max_attempts = st.selectbox(
            "Max Re-cluster Attempts",
            options=[1, 2, 3],
            index=2,
            key="cfg_max_attempts",
        )

        silhouette_thresh = st.slider(
            "Silhouette Threshold",
            min_value=0.1,
            max_value=0.6,
            value=0.3,
            step=0.05,
            key="cfg_silhouette",
        )

        st.markdown("<hr style='border-color:#27272a;margin:1rem 0;'>", unsafe_allow_html=True)

        st.markdown("""
        <p style="font-size:0.7rem;color:#27272a;line-height:1.5;margin:0;">
            Shiv Nadar University Chennai<br>
            <span style="color:#27272a;">AI_DS_024</span>
        </p>
        """, unsafe_allow_html=True)

    return {"max_attempts": max_attempts, "silhouette_threshold": silhouette_thresh}


# ---------------------------------------------------------------------------
# Pipeline runner (runs in main thread via st.status blocks)
# ---------------------------------------------------------------------------

def run_pipeline_with_ui(video_path: str, feedback: dict = None):
    import sys
    sys.path.insert(0, ".")

    from src.config.settings import settings
    from src.handlers.pipeline_handler import PipelineHandler

    # Apply sidebar config overrides
    settings.MAX_RECLUSTER_ATTEMPTS = st.session_state.get("cfg_max_attempts", 3)
    settings.SILHOUETTE_THRESHOLD = st.session_state.get("cfg_silhouette", 0.3)

    pipeline_placeholder = st.empty()

    # Stage containers
    s1_col, s2_col = st.columns([1, 1])

    # We use a list to collect state between callbacks
    state_holder = {}
    agent1_events = []

    def callback(step: str, data: dict):
        # Store data for later rendering
        if step == "stage_complete" and data.get("stage") == "transcription":
            st.session_state.transcript = data.get("data", [])
            set_stage_status("transcription", "complete")

        elif step == "stage_complete" and data.get("stage") == "clustering":
            st.session_state.clusters = data.get("data", [])
            set_stage_status("clustering", "complete")

        elif step == "metrics_computed":
            st.session_state.metrics = data.get("metrics", {})

        elif step == "agent1_instructions":
            agent1_events.append(data)
            st.session_state.agent1_events = agent1_events

        elif step == "agent1_passed":
            set_stage_status("agent1_eval", "complete")

        elif step == "agent1_stalled":
            # Scores frozen — record it as a special event and close the stage
            agent1_events.append({
                "stalled": True,
                "attempt": data.get("attempt"),
                "reason": data.get("reason", "Scores unchanged — geometry is frozen."),
            })
            st.session_state.agent1_events = agent1_events
            set_stage_status("agent1_eval", "complete")

        elif step == "reclustered":
            # Track per-attempt relabel map so it can be shown in the UI
            attempt = data.get("attempt", 0)
            relabel_map = data.get("relabel_map", {})
            if relabel_map:
                existing = st.session_state.get("relabel_history", [])
                existing.append({"attempt": attempt, "relabels": relabel_map})
                st.session_state.relabel_history = existing

        elif step == "stage_complete" and data.get("stage") == "summarization":
            st.session_state.summaries = data.get("data", [])
            set_stage_status("summarization", "complete")

        elif step == "stage_complete" and data.get("stage") == "tts":
            st.session_state.tts_paths = data.get("paths", {})
            set_stage_status("tts", "complete")

        elif step == "stage_complete" and data.get("stage") == "video_processing":
            st.session_state.video_results = data.get("results", {})
            set_stage_status("video_processing", "complete")

        elif step == "pipeline_complete":
            st.session_state.pipeline_complete = True
            st.session_state.run_id = data.get("run_id")

    handler = PipelineHandler(progress_callback=callback)

    # Stage 1: Audio Extraction
    with st.status("Audio extraction in progress...", expanded=True) as s1:
        set_stage_status("audio_extraction", "running")
        try:
            from src.services.audio_extractor import extract_audio
            from src.utils.file_utils import generate_run_id, ensure_output_dirs
            from src.config.settings import settings as cfg

            run_id = generate_run_id()
            st.session_state.run_id = run_id
            dirs = ensure_output_dirs(cfg.BASE_OUTPUT_DIR, run_id)
            state_holder["run_id"] = run_id
            state_holder["dirs"] = dirs

            log_to_ui("Extracting audio track from video using ffmpeg", "info")
            raw_audio = str(dirs["audio"] / "raw.wav")
            extract_audio(video_path, raw_audio)
            state_holder["raw_audio"] = raw_audio

            log_to_ui(f"Audio saved: {raw_audio}", "success")
            s1.update(label="Audio extraction complete", state="complete", expanded=False)
            set_stage_status("audio_extraction", "complete")
        except Exception as exc:
            s1.update(label=f"Audio extraction failed: {exc}", state="error")
            set_stage_status("audio_extraction", "failed")
            st.error(f"Audio extraction failed: {exc}")
            return

    # Stage 2: Preprocessing
    with st.status("Voice preprocessing in progress...", expanded=True) as s2:
        set_stage_status("preprocessing", "running")
        try:
            from src.services.preprocessor import preprocess_audio

            log_to_ui("Applying noise reduction", "info")
            clean_audio = str(dirs["audio"] / "clean.wav")
            log_to_ui("Running voice activity detection (Silero VAD)", "info")
            preprocess_audio(raw_audio, clean_audio)
            state_holder["clean_audio"] = clean_audio

            log_to_ui("Voice preprocessing complete", "success")
            s2.update(label="Voice preprocessing complete", state="complete", expanded=False)
            set_stage_status("preprocessing", "complete")
        except Exception as exc:
            s2.update(label=f"Preprocessing failed: {exc}", state="error")
            set_stage_status("preprocessing", "failed")
            st.error(f"Preprocessing failed: {exc}")
            return

    # Stage 3: Transcription
    with st.status("Transcription in progress...", expanded=True) as s3:
        set_stage_status("transcription", "running")
        try:
            from src.services.transcriber import transcribe
            from src.utils.file_utils import save_json
            from dataclasses import asdict

            log_to_ui("Loading Whisper medium model", "info")
            log_to_ui("Transcribing audio with word-level timestamps", "info")
            segments = transcribe(clean_audio)
            transcript_data = [asdict(s) for s in segments]
            save_json(transcript_data, dirs["text"] / "transcript.json")
            st.session_state.transcript = transcript_data
            state_holder["segments"] = segments

            log_to_ui(f"Punctuation restored | {len(segments)} segments extracted", "success")

            # Inline preview
            st.markdown("""
            <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                      text-transform:uppercase;letter-spacing:0.07em;margin:0.75rem 0 0.4rem 0;">
                Transcript Preview (first 3 segments)
            </p>
            """, unsafe_allow_html=True)
            for seg in transcript_data[:3]:
                st.markdown(f"""
                <div style="
                    background:#09090b;border:1px solid #27272a;border-radius:5px;
                    padding:0.45rem 0.75rem;margin-bottom:0.35rem;
                    font-size:0.8rem;color:#94a3b8;font-family:'JetBrains Mono',monospace;
                ">
                    [{seg['start_time']:.2f}s - {seg['end_time']:.2f}s] {seg['sentence']}
                </div>
                """, unsafe_allow_html=True)

            transcript_json_str = json.dumps(transcript_data, indent=2)
            col1, col2 = st.columns([3, 1])
            with col2:
                st.download_button(
                    "Export Transcript",
                    data=transcript_json_str,
                    file_name="transcript.json",
                    mime="application/json",
                    key="dl_transcript",
                )

            s3.update(label=f"Transcription complete — {len(segments)} segments", state="complete", expanded=False)
            set_stage_status("transcription", "complete")
        except Exception as exc:
            s3.update(label=f"Transcription failed: {exc}", state="error")
            set_stage_status("transcription", "failed")
            st.error(f"Transcription failed: {exc}")
            return

    sentences = [s.sentence for s in state_holder["segments"]]

    # Stage 4: Embedding + Clustering
        
    with st.status("Embedding and clustering in progress...", expanded=True) as s4:
        set_stage_status("clustering", "running")
        try:
            import numpy as np
            from src.services.embedder import embed_sentences
            from src.services.clusterer import cluster_and_categorize
            from src.utils.file_utils import save_json
            from src.config.settings import settings as cfg
            from dataclasses import asdict

            log_to_ui(f"Encoding {len(sentences)} sentences with SBERT (all-MiniLM-L6-v2)", "info")
            prog = st.progress(0, text="Generating embeddings...")
            embeddings = embed_sentences(sentences)
            prog.progress(30, text="Running sliding window zero-shot classification...")

            log_to_ui(f"Classifying sentence windows (size={cfg.WINDOW_SIZE}, overlap={cfg.WINDOW_OVERLAP})", "info")

            prog.progress(55, text="Detecting boundary misfits via cosine similarity...")
            log_to_ui("Detecting and reassigning boundary misfit sentences", "info")

            prog.progress(75, text="Running intra-category HDBSCAN sub-clustering...")
            log_to_ui("Applying HDBSCAN within each category group", "info")

            # cluster_and_categorize now returns (clusters, integer_labels, base_refined_labels)
            clusters, labels, base_labels = cluster_and_categorize(
                state_holder["segments"],
                embeddings,
                cfg.HDBSCAN_MIN_CLUSTER_SIZE,
                cfg.HDBSCAN_MIN_SAMPLES,
            )
            prog.progress(100, text="Clustering complete")

            cluster_data = [asdict(c) for c in clusters]
            save_json(cluster_data, dirs["text"] / "clusters.json")
            st.session_state.clusters = cluster_data
            st.session_state.embeddings = embeddings  # Store for visualization
            state_holder["clusters"] = clusters
            state_holder["embeddings"] = embeddings
            state_holder["labels"] = labels
            state_holder["base_labels"] = base_labels  # Cache for fast retries
            state_holder["min_cls"] = cfg.HDBSCAN_MIN_CLUSTER_SIZE
            state_holder["min_smp"] = cfg.HDBSCAN_MIN_SAMPLES

            log_to_ui(f"Discovered {len(clusters)} topic clusters", "success")
            
            # Show cluster visualization
            st.markdown("**Cluster Visualization**")
            fig = render_cluster_visualization(cluster_data, embeddings)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="cluster_viz_pipeline")

            st.markdown(f"""
            <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                      text-transform:uppercase;letter-spacing:0.07em;margin:0.75rem 0 0.5rem 0;">
                Cluster Details
            </p>
            """, unsafe_allow_html=True)
            for i, c in enumerate(clusters):
                render_cluster_card(asdict(c), i)

            col1, col2 = st.columns([3, 1])
            with col2:
                st.download_button(
                    "Export Clusters",
                    data=json.dumps(cluster_data, indent=2),
                    file_name="clusters.json",
                    mime="application/json",
                    key="dl_clusters",
                )

            s4.update(
                label=f"Clustering complete — {len(clusters)} categories identified",
                state="complete",
                expanded=False,
            )
            set_stage_status("clustering", "complete")
        except Exception as exc:
            s4.update(label=f"Clustering failed: {exc}", state="error")
            set_stage_status("clustering", "failed")
            st.error(f"Clustering failed: {exc}")
            return


    # Stage 5: Agent 1 Evaluation Loop
    with st.status("Agent 1 evaluation in progress...", expanded=True) as s5:
        set_stage_status("agent1_eval", "running")
        try:
            import numpy as np
            from src.services.metrics import compute_metrics
            from src.services.agent1 import run_agent1
            from src.services.clusterer import apply_relabel_and_cluster
            from src.config.settings import settings as cfg
            from dataclasses import asdict

            clusters    = state_holder["clusters"]
            embeddings  = state_holder["embeddings"]
            labels      = state_holder["labels"]
            base_labels = state_holder["base_labels"]  # cached from first classification
            min_cls     = state_holder["min_cls"]
            min_smp     = state_holder["min_smp"]
            prev_labels = None
            final_clusters = clusters

            # Accumulate relabel suggestions across all attempts
            cumulative_relabel: dict = {}
            # Track metric fingerprint to detect frozen (unchanging) scores
            prev_score_sig = None

            for attempt in range(cfg.MAX_RECLUSTER_ATTEMPTS):
                log_to_ui(f"Computing evaluation metrics (attempt {attempt + 1})", "info")
                metrics = compute_metrics(clusters, embeddings, labels, prev_labels)
                metrics_dict = asdict(metrics)
                st.session_state.metrics = metrics_dict

                # Render metric cards
                st.markdown(f"""
                <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                          text-transform:uppercase;letter-spacing:0.07em;margin:0.75rem 0 0.5rem 0;">
                    Evaluation Metrics &mdash; Attempt {attempt + 1}
                </p>
                """, unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                with m1:
                    sil = metrics.silhouette_overall
                    render_metric_card(
                        "Silhouette Score",
                        f"{sil:.3f}",
                        status="good" if sil >= cfg.SILHOUETTE_THRESHOLD else "bad",
                        delta_text="Above threshold" if sil >= cfg.SILHOUETTE_THRESHOLD else f"Below {cfg.SILHOUETTE_THRESHOLD} threshold",
                    )
                with m2:
                    dbi = metrics.dbi
                    render_metric_card(
                        "Davies-Bouldin Index",
                        f"{dbi:.3f}",
                        status="good" if dbi <= cfg.DBI_THRESHOLD else "bad",
                        delta_text="Good separation" if dbi <= cfg.DBI_THRESHOLD else "Poor separation",
                    )
                with m3:
                    noise = metrics.noise_pct
                    render_metric_card(
                        "Noise Percentage",
                        f"{noise:.1f}%",
                        status="good" if noise <= cfg.NOISE_PCT_THRESHOLD else "bad",
                        delta_text="Within limit" if noise <= cfg.NOISE_PCT_THRESHOLD else "Exceeds limit",
                    )

                m4, m5, m6 = st.columns(3)
                with m4:
                    ch = metrics.ch_index
                    render_metric_card("CH Index", f"{ch:.1f}", status="good" if ch > 1 else "warn")
                with m5:
                    if metrics.ami is not None:
                        render_metric_card("AMI Stability", f"{metrics.ami:.3f}",
                                           status="good" if metrics.ami > 0.7 else "warn")
                    else:
                        render_metric_card("AMI Stability", "N/A", status="neutral",
                                           delta_text="First run")
                with m6:
                    if metrics.nmi is not None:
                        render_metric_card("NMI Stability", f"{metrics.nmi:.3f}",
                                           status="good" if metrics.nmi > 0.7 else "warn")
                    else:
                        render_metric_card("NMI Stability", "N/A", status="neutral",
                                           delta_text="First run")

                # Per-cluster coherence
                if metrics.per_cluster_coherence:
                    st.markdown("""
                    <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                              text-transform:uppercase;letter-spacing:0.07em;margin:0.75rem 0 0.4rem 0;">
                        Per-Cluster Coherence (c_v)
                    </p>
                    """, unsafe_allow_html=True)
                    for cat, score in metrics.per_cluster_coherence.items():
                        bar_color = "#10b981" if score >= 0.6 else "#d97706" if score >= 0.4 else "#ef4444"
                        bar_width = int(score * 100)
                        st.markdown(f"""
                        <div style="margin-bottom:0.4rem;">
                            <div style="display:flex;justify-content:space-between;
                                        margin-bottom:0.2rem;">
                                <span style="font-size:0.78rem;color:#94a3b8;">{cat}</span>
                                <span style="font-size:0.75rem;color:{bar_color};
                                             font-family:'JetBrains Mono',monospace;
                                             font-weight:600;">{score:.3f}</span>
                            </div>
                            <div style="background:#27272a;border-radius:3px;height:5px;">
                                <div style="background:{bar_color};width:{bar_width}%;
                                            height:5px;border-radius:3px;
                                            transition:width 0.5s;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                if metrics.passed:
                    log_to_ui("All metrics passed. Clustering is satisfactory.", "success")
                    final_clusters = clusters
                    break

                # --- Early-exit: frozen geometry detection ---
                current_score_sig = (
                    round(metrics.silhouette_overall or 0, 6),
                    round(metrics.dbi or 0, 6),
                    round(metrics.ch_index or 0, 6),
                )
                if prev_score_sig is not None and current_score_sig == prev_score_sig:
                    log_to_ui(
                        "Scores identical to previous attempt — geometry is frozen. "
                        "Stopping retry loop early.", "warn"
                    )
                    final_clusters = clusters
                    break
                prev_score_sig = current_score_sig

                # Failure report
                st.markdown("""
                <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                          text-transform:uppercase;letter-spacing:0.07em;margin:0.75rem 0 0.4rem 0;">
                    Failure Analysis
                </p>
                """, unsafe_allow_html=True)
                for reason in (metrics.failure_reasons or []):
                    log_to_ui(reason, "warn")

                if attempt < cfg.MAX_RECLUSTER_ATTEMPTS - 1:
                    log_to_ui(f"Invoking LLM Agent 1 for diagnosis (attempt {attempt + 1})", "info")
                    instructions = run_agent1(clusters, metrics, min_cls, min_smp)
                    render_agent_diagnosis(instructions, attempt + 1)

                    # Update HDBSCAN params
                    if instructions.get("new_min_cluster_size"):
                        min_cls = int(instructions["new_min_cluster_size"])
                    if instructions.get("new_min_samples"):
                        min_smp = int(instructions["new_min_samples"])

                    # Accumulate relabel_suggestions (transitive)
                    for old_lbl, new_lbl in (instructions.get("relabel_suggestions") or {}).items():
                        for k in list(cumulative_relabel.keys()):
                            if cumulative_relabel[k] == old_lbl:
                                cumulative_relabel[k] = new_lbl
                        cumulative_relabel[old_lbl] = new_lbl

                    # Convert merge_pairs into relabel entries
                    for pair in (instructions.get("merge_pairs") or []):
                        if len(pair) == 2:
                            keep_lbl, drop_lbl = pair[0], pair[1]
                            for k in list(cumulative_relabel.keys()):
                                if cumulative_relabel[k] == drop_lbl:
                                    cumulative_relabel[k] = keep_lbl
                            cumulative_relabel[drop_lbl] = keep_lbl
                            log_to_ui(
                                f"Merging cluster '{drop_lbl}' into '{keep_lbl}'", "info"
                            )

                    if cumulative_relabel:
                        relabel_str = " | ".join(f"{k} -> {v}" for k, v in cumulative_relabel.items())
                        log_to_ui(f"Relabels: {relabel_str}", "info")

                    prev_labels = labels.copy()

                    # Fast retry: skip sliding-window, only re-run HDBSCAN
                    clusters, labels = apply_relabel_and_cluster(
                        state_holder["segments"],
                        embeddings,
                        base_labels,
                        relabel_map=cumulative_relabel if cumulative_relabel else None,
                        min_cluster_size=min_cls,
                        min_samples=min_smp,
                    )

                    log_to_ui(f"Re-clustering applied. New cluster count: {len(clusters)}", "info")
                    final_clusters = clusters
                else:
                    log_to_ui("Max re-cluster attempts reached. Proceeding with best result.", "warn")
                    final_clusters = clusters

            state_holder["final_clusters"] = final_clusters
            st.session_state.clusters = [asdict(c) for c in final_clusters]

            s5.update(label="Agent 1 evaluation complete", state="complete", expanded=False)
            set_stage_status("agent1_eval", "complete")
        except Exception as exc:
            s5.update(label=f"Agent 1 evaluation failed: {exc}", state="error")
            set_stage_status("agent1_eval", "failed")
            st.error(f"Agent 1 evaluation failed: {exc}")
            return

    # Stage 6: Summarization
    with st.status("Summarization in progress...", expanded=True) as s6:
        set_stage_status("summarization", "running")
        try:
            from src.services.summarizer import summarize_cluster
            from src.services.agent2 import run_agent2
            from src.utils.file_utils import save_json
            from src.config.settings import settings as cfg
            from dataclasses import asdict

            final_clusters = state_holder["final_clusters"]
            feedback = feedback or {}
            summaries = []
            prog = st.progress(0, text="Initializing summarization...")

            for idx, cluster in enumerate(final_clusters):
                prog.progress(
                    int(((idx) / len(final_clusters)) * 100),
                    text=f"Summarizing: {cluster.category}",
                )
                log_to_ui(f"Summarizing cluster: {cluster.category} ({len(cluster.sentences)} sentences)", "info")

                depth = int(feedback.get(cluster.category, {}).get("depth", 3))
                custom_note = feedback.get(cluster.category, {}).get("note", "")

                summary = summarize_cluster(cluster)

                needs_agent = (
                    summary.rouge_scores["rougeL"] < cfg.ROUGE_L_THRESHOLD
                    or depth != 3
                    or bool(custom_note.strip())
                )

                if needs_agent:
                    log_to_ui(f"Agent 2 invoked for '{cluster.category}' (ROUGE-L={summary.rouge_scores['rougeL']:.3f}, depth={depth})", "info")
                    from src.handlers.pipeline_handler import _compute_token_budget
                    token_budget = _compute_token_budget(feedback, cluster.category)
                    summary = run_agent2(
                        cluster,
                        depth_level=depth,
                        custom_note=custom_note,
                        max_tokens=token_budget,
                    )
                    log_to_ui(f"Agent 2 complete for '{cluster.category}' | ROUGE-L={summary.rouge_scores['rougeL']:.3f}", "success")

                summaries.append(summary)

            prog.progress(100, text="All categories summarized")
            summary_data = [asdict(s) for s in summaries]
            save_json(summary_data, dirs["summaries"] / "summaries.json")
            st.session_state.summaries = summary_data
            state_holder["summaries"] = summaries

            s6.update(label=f"Summarization complete — {len(summaries)} categories", state="complete", expanded=False)
            set_stage_status("summarization", "complete")
        except Exception as exc:
            s6.update(label=f"Summarization failed: {exc}", state="error")
            set_stage_status("summarization", "failed")
            st.error(f"Summarization failed: {exc}")
            return

    # Stage 7: TTS
    with st.status("Text-to-speech synthesis in progress...", expanded=True) as s7:
        set_stage_status("tts", "running")
        try:
            from src.services.tts_engine import synthesize_all

            summaries = state_holder["summaries"]
            summary_texts = {s.category: s.abstractive_summary for s in summaries}

            prog = st.progress(0, text="Loading Coqui TTS model...")
            log_to_ui("Synthesizing audio for all categories", "info")

            tts_paths = synthesize_all(summary_texts, str(dirs["tts"]))
            st.session_state.tts_paths = tts_paths
            prog.progress(100, text="TTS synthesis complete")

            for cat, path in tts_paths.items():
                status_text = "Generated" if path and Path(path).exists() else "Failed"
                level = "success" if status_text == "Generated" else "error"
                log_to_ui(f"{cat}: {status_text}", level)

            s7.update(label="Text-to-speech synthesis complete", state="complete", expanded=False)
            set_stage_status("tts", "complete")
        except Exception as exc:
            s7.update(label=f"TTS failed: {exc}", state="error")
            set_stage_status("tts", "failed")
            st.error(f"TTS generation failed: {exc}")
            return

    # Stage 8: Video Processing
    with st.status("Video compilation in progress...", expanded=True) as s8:
        set_stage_status("video_processing", "running")
        try:
            from src.services.video_processor import process_video_pipeline
            prog = st.progress(0, text="Extracting keyframes and compiling summary videos...")
            log_to_ui("Aligning sentences to original video timeline", "info")

            video_output_dir = dirs["video"]
            video_results = process_video_pipeline(video_path, clusters, video_output_dir, tts_paths=tts_paths)
            st.session_state.video_results = {k: asdict(v) for k, v in video_results.items()}
            
            prog.progress(100, text="Video compilation complete")

            for cat, res in video_results.items():
                if res.summary_video_path and Path(res.summary_video_path).exists():
                    log_to_ui(f"{cat}: Compiled {len(res.segments)} video segments", "success")
                else:
                    log_to_ui(f"{cat}: Failed to compile video", "error")

            s8.update(label="Video compilation complete", state="complete", expanded=False)
            set_stage_status("video_processing", "complete")
        except Exception as exc:
            s8.update(label=f"Video pipeline failed: {exc}", state="error")
            set_stage_status("video_processing", "failed")
            st.error(f"Video pipeline failed: {exc}")
            return

    st.session_state.pipeline_running = False
    st.session_state.pipeline_complete = True
    st.toast("Pipeline completed successfully", icon=None)


def render_log_entry_html(message: str, level: str = "info") -> str:
    """Return an HTML string for a log line (used inside st.status blocks)."""
    colors = {"info": "#3b82f6", "success": "#10b981", "warn": "#f59e0b", "error": "#ef4444"}
    prefixes = {"info": "INFO", "success": "DONE", "warn": "WARN", "error": "ERR "}
    color = colors.get(level, "#3b82f6")
    prefix = prefixes.get(level, "INFO")
    ts = time.strftime("%H:%M:%S")
    return f"""
    <div style="
        display:flex;gap:10px;padding:0.25rem 0;
        border-bottom:1px solid #09090b;
        font-family:'JetBrains Mono',monospace;font-size:0.76rem;
    ">
        <span style="color:#27272a;white-space:nowrap;">{ts}</span>
        <span style="color:{color};font-weight:600;white-space:nowrap;">{prefix}</span>
        <span style="color:#94a3b8;">{message}</span>
    </div>
    """


def log_to_ui(message: str, level: str = "info"):
    """Display a log message in the UI with proper formatting."""
    prefixes = {"info": "[INFO]", "success": "[DONE]", "warn": "[WARN]", "error": "[ERROR]"}
    colors = {"info": "#3b82f6", "success": "#10b981", "warn": "#f59e0b", "error": "#ef4444"}
    
    prefix = prefixes.get(level, "[INFO]")
    color = colors.get(level, "#3b82f6")
    ts = time.strftime("%H:%M:%S")
    
    st.markdown(f"""
    <div style="
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        padding: 0.25rem 0;
        color: #94a3b8;
    ">
        <span style="color: #71717a;">{ts}</span>
        <span style="color: {color}; font-weight: 600; margin: 0 0.5rem;">{prefix}</span>
        <span>{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_cluster_visualization(clusters, embeddings):
    """Create an interactive 2D visualization of clusters using UMAP + Plotly."""
    try:
        import plotly.graph_objects as go
        from umap import UMAP
        import numpy as np
        
        # Reduce embeddings to 2D using UMAP
        reducer = UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
        embeddings_2d = reducer.fit_transform(embeddings)
        
        # Prepare data for plotting
        categories = []
        x_coords = []
        y_coords = []
        texts = []
        
        for cluster in clusters:
            category = cluster.get("category", "Unknown")
            sentences = cluster.get("sentences", [])
            
            for sent in sentences:
                # Find the index of this sentence in the original embeddings
                # This is a simplified approach - you may need to match by content
                categories.append(category)
                texts.append(sent[:100] + "..." if len(sent) > 100 else sent)
        
        # Create color mapping for categories
        unique_categories = list(set(categories))
        colors = [f"hsl({i * 360 / len(unique_categories)}, 70%, 50%)" for i in range(len(unique_categories))]
        color_map = {cat: colors[i] for i, cat in enumerate(unique_categories)}
        
        # Create the plot
        fig = go.Figure()
        
        for category in unique_categories:
            mask = [c == category for c in categories]
            indices = [i for i, m in enumerate(mask) if m]
            
            fig.add_trace(go.Scatter(
                x=embeddings_2d[indices, 0],
                y=embeddings_2d[indices, 1],
                mode='markers',
                name=category,
                marker=dict(
                    size=8,
                    color=color_map[category],
                    line=dict(width=0.5, color='white')
                ),
                text=[texts[i] for i in indices],
                hovertemplate='<b>%{text}</b><br>Category: ' + category + '<extra></extra>'
            ))
        
        fig.update_layout(
            title="Cluster Visualization (UMAP 2D Projection)",
            xaxis_title="UMAP Dimension 1",
            yaxis_title="UMAP Dimension 2",
            hovermode='closest',
            template="plotly_dark",
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Failed to create visualization: {e}")
        return None


# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

def render_results_panel():
    if not st.session_state.pipeline_complete:
        return

    st.markdown("<hr style='border-color:#27272a;margin:2rem 0 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.25rem;">
        <h2 style="margin:0 0 0.25rem 0;font-size:1.1rem;color:#ffffff;">Pipeline Results</h2>
        <p style="margin:0;font-size:0.8rem;color:#a1a1aa;">
            All outputs from the completed pipeline run. Each artifact is available for download.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Transcript", "Clusters", "Summaries & Audio", "Video Results", "Raw Metrics"])

    with tab1:
        transcript = st.session_state.get("transcript", [])
        if transcript:
            st.markdown(f"""
            <p style="font-size:0.78rem;color:#71717a;margin-bottom:0.75rem;">
                {len(transcript)} segments extracted
            </p>
            """, unsafe_allow_html=True)
            for seg in transcript:
                st.markdown(f"""
                <div style="
                    display:flex;gap:12px;align-items:flex-start;
                    padding:0.5rem 0.75rem;
                    background:#121214;border:1px solid #27272a;border-radius:6px;
                    margin-bottom:0.35rem;
                ">
                    <span style="
                        font-size:0.7rem;color:#27272a;white-space:nowrap;
                        font-family:'JetBrains Mono',monospace;padding-top:1px;
                    ">{seg['start_time']:.1f}s</span>
                    <span style="font-size:0.83rem;color:#a1a1aa;line-height:1.5;">{seg['sentence']}</span>
                </div>
                """, unsafe_allow_html=True)

            st.download_button(
                "Export Full Transcript (JSON)",
                data=json.dumps(transcript, indent=2),
                file_name="transcript.json",
                mime="application/json",
                key="results_dl_transcript",
            )

    with tab2:
        clusters = st.session_state.get("clusters", [])
        embeddings = st.session_state.get("embeddings", None)
        
        if clusters:
            # Show visualization if embeddings are available
            if embeddings is not None:
                st.markdown("**Interactive Cluster Visualization**")
                fig = render_cluster_visualization(clusters, embeddings)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="cluster_viz_results")
                st.markdown("<hr style='border-color:#27272a;margin:1.5rem 0;'>", unsafe_allow_html=True)
            
            st.markdown("**Cluster Details**")
            for i, c in enumerate(clusters):
                render_cluster_card(c, i)
                with st.expander(f"All sentences — {c['category']}"):
                    for sent in c.get("sentences", []):
                        st.markdown(f"""
                        <div style="
                            padding:0.35rem 0.65rem;background:#09090b;
                            border-left:2px solid #27272a;
                            margin-bottom:0.25rem;font-size:0.8rem;color:#94a3b8;
                        ">{sent}</div>
                        """, unsafe_allow_html=True)

            st.download_button(
                "Export Clusters (JSON)",
                data=json.dumps(clusters, indent=2),
                file_name="clusters.json",
                mime="application/json",
                key="results_dl_clusters",
            )

    with tab3:
        summaries = st.session_state.get("summaries", [])
        tts_paths = st.session_state.get("tts_paths", {})
        video_results = st.session_state.get("video_results", {})
        
        if summaries:
            for i, s in enumerate(summaries):
                cat = s["category"]
                tts_path = tts_paths.get(cat) if tts_paths else None
                video_res = video_results.get(cat) if video_results else None
                render_summary_card(s, tts_path, video_result=video_res, idx=i)

            all_summaries_json = json.dumps(summaries, indent=2)
            st.download_button(
                "Export All Summaries (JSON)",
                data=all_summaries_json,
                file_name="all_summaries.json",
                mime="application/json",
                key="results_dl_all_summaries",
            )

    with tab4:
        # ── Video Results ─────────────────────────────────────────────────────
        video_results = st.session_state.get("video_results", {})

        if not video_results:
            st.markdown("""
            <div style="
                text-align:center;padding:3rem 1rem;
                color:#3f3f46;font-size:0.9rem;
            ">
                Video results will appear here after the pipeline completes.
            </div>
            """, unsafe_allow_html=True)
        else:
            for cat, vr in video_results.items():
                summary_video_path = vr.get("summary_video_path", "")
                keyframes          = vr.get("keyframes", [])
                segments           = vr.get("segments", [])

                # ── Category header ──────────────────────────────────────────
                st.markdown(f"""
                <div style="
                    display:flex;align-items:center;gap:10px;
                    padding:1.1rem 1.25rem;background:#121214;
                    border:1px solid #27272a;border-radius:10px;
                    margin-bottom:1rem;
                ">
                    <div style="
                        width:32px;height:32px;border-radius:8px;
                        background:linear-gradient(135deg,rgba(124,58,237,.25),rgba(79,70,229,.25));
                        border:1px solid rgba(124,58,237,.4);
                        display:flex;align-items:center;justify-content:center;
                    ">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                             stroke="#a78bfa" stroke-width="2"
                             stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="23 7 16 12 23 17 23 7"/>
                            <rect x="1" y="5" width="15" height="14" rx="2"/>
                        </svg>
                    </div>
                    <div>
                        <p style="margin:0;font-size:0.95rem;font-weight:600;color:#fff;">{cat}</p>
                        <p style="margin:0;font-size:0.72rem;color:#52525b;">
                            {len(segments)} merged segment(s) &middot; {len(keyframes)} keyframes extracted
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Compiled summary video ────────────────────────────────────
                if summary_video_path and Path(summary_video_path).exists():
                    st.markdown("""
                    <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                              text-transform:uppercase;letter-spacing:0.07em;margin:0 0 0.5rem 0;">
                        Compiled Summary Video
                    </p>
                    """, unsafe_allow_html=True)
                    st.video(summary_video_path)

                    with open(summary_video_path, "rb") as vf:
                        st.download_button(
                            label=f"Download {cat} Summary Video",
                            data=vf,
                            file_name=Path(summary_video_path).name,
                            mime="video/mp4",
                            key=f"tab4_dl_vid_{cat}",
                        )
                else:
                    st.warning(f"Summary video for '{cat}' was not generated or the file is missing.")

                # ── Segments timeline ─────────────────────────────────────────
                if segments:
                    with st.expander(f"Timeline segments — {cat}"):
                        for seg_start, seg_end in segments:
                            st.markdown(f"""
                            <div style="
                                display:inline-block;background:#09090b;
                                border:1px solid #27272a;border-radius:5px;
                                padding:0.25rem 0.75rem;margin:0.2rem;
                                font-size:0.78rem;color:#94a3b8;
                                font-family:'JetBrains Mono',monospace;
                            ">{seg_start:.2f}s &rarr; {seg_end:.2f}s</div>
                            """, unsafe_allow_html=True)

                # ── Keyframes grid ────────────────────────────────────────────
                if keyframes:
                    st.markdown("""
                    <p style="font-size:0.78rem;font-weight:600;color:#a1a1aa;
                              text-transform:uppercase;letter-spacing:0.07em;margin:1rem 0 0.5rem 0;">
                        Extracted Keyframes (3 per sentence)
                    </p>
                    """, unsafe_allow_html=True)

                    # Group frames by sentence text
                    import itertools
                    for sent_text, group_iter in itertools.groupby(
                        keyframes, key=lambda x: x.get("text", "")
                    ):
                        group_frames = list(group_iter)
                        # Sentence label
                        st.markdown(f"""
                        <div style="
                            font-size:0.8rem;color:#71717a;
                            border-left:2px solid #27272a;
                            padding-left:0.65rem;margin:0.75rem 0 0.35rem 0;
                        ">{sent_text}</div>
                        """, unsafe_allow_html=True)
                        # 3-column frame row
                        cols = st.columns(3)
                        for frame_info, col in zip(group_frames, cols):
                            fp = frame_info.get("frame_path", "")
                            if fp and Path(fp).exists():
                                ftype = frame_info.get("frame_type", "")
                                ts    = frame_info.get("timestamp", 0)
                                col.image(
                                    fp,
                                    caption=f"{ftype.capitalize()} @ {ts:.2f}s",
                                    use_container_width=True,
                                )

                st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)

    with tab5:
        metrics = st.session_state.get("metrics", {})
        if metrics:
            st.json(metrics)
            st.download_button(
                "Export Metrics (JSON)",
                data=json.dumps(metrics, indent=2),
                file_name="metrics.json",
                mime="application/json",
                key="results_dl_metrics",
            )


# ---------------------------------------------------------------------------
# User feedback panel
# ---------------------------------------------------------------------------

def render_feedback_panel():
    if not st.session_state.pipeline_complete:
        return

    clusters = st.session_state.get("clusters", [])
    if not clusters:
        return

    st.markdown("<hr style='border-color:#27272a;margin:2rem 0 1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:1.25rem;">
        <h2 style="margin:0 0 0.25rem 0;font-size:1.1rem;color:#ffffff;">Personalise Summary</h2>
        <p style="margin:0;font-size:0.8rem;color:#a1a1aa;">
            Adjust the depth of coverage per topic and optionally add a focus instruction.
            Re-running will only regenerate categories you have modified.
        </p>
    </div>
    """, unsafe_allow_html=True)

    categories = list({c["category"] for c in clusters})
    prefs = {}

    for category in categories:
        st.markdown(f"""
        <div style="
            background:#121214;border:1px solid #27272a;border-radius:8px;
            padding:1rem 1.15rem;margin-bottom:0.75rem;
        ">
            <p style="margin:0 0 0.65rem 0;font-size:0.875rem;font-weight:600;color:#ffffff;">
                {category}
            </p>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns([2, 3])
        with col_a:
            depth = st.select_slider(
                "Detail level",
                options=[1, 2, 3, 4, 5],
                value=3,
                key=f"fb_depth_{category}",
                help="1 = Brief | 3 = Standard | 5 = Comprehensive",
                label_visibility="collapsed",
            )
            depth_labels = {
                1: "Brief — one sentence",
                2: "Short — 2 to 3 sentences",
                3: "Standard — balanced summary",
                4: "Detailed — full paragraph",
                5: "Comprehensive — full analysis",
            }
            st.markdown(f"""
            <p style="font-size:0.72rem;color:#a1a1aa;margin-top:0.3rem;">{depth_labels[depth]}</p>
            """, unsafe_allow_html=True)

        with col_b:
            note = st.text_input(
                "Focus instruction (optional)",
                key=f"fb_note_{category}",
                placeholder="e.g. Focus on economic impact",
                label_visibility="collapsed",
            )

        prefs[category] = {"depth": depth, "note": note}
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.25rem;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1.5, 3])
    with col1:
        if st.button("Apply Preferences", key="btn_apply_feedback", use_container_width=True):
            unchanged = all(
                prefs[cat]["depth"] == 3 and not prefs[cat]["note"].strip()
                for cat in prefs
            )
            if unchanged:
                st.info("No changes detected. Adjust depth or add a focus instruction to personalise.")
            else:
                st.session_state.feedback_prefs = prefs
                st.session_state.pipeline_complete = False
                st.session_state.pipeline_running = True

                # Reset only affected stage statuses
                st.session_state.stage_statuses["summarization"] = "pending"
                st.session_state.stage_statuses["tts"] = "pending"
                st.rerun()

    with col2:
        if st.button("Reset Preferences", key="btn_reset_feedback", use_container_width=True):
            for category in categories:
                if f"fb_depth_{category}" in st.session_state:
                    del st.session_state[f"fb_depth_{category}"]
                if f"fb_note_{category}" in st.session_state:
                    del st.session_state[f"fb_note_{category}"]
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main app entry point
# ---------------------------------------------------------------------------

def render_app_page():
    """The full application page with sidebar and pipeline controls."""
    cfg = render_sidebar()
    render_app_header()

    # Add a back button
    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back to Home", key="btn_back_home"):
            st.session_state.current_page = "landing"
            st.rerun()

    # ── Upload Section ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        padding: 0 0 1.5rem 0;
        border-bottom: 1px solid #111111;
        margin-bottom: 2rem;
    ">
        <h2 style="margin:0 0 0.4rem 0;font-size:1.1rem;color:#ffffff;font-weight:600;">Video Input</h2>
        <p style="margin:0;font-size:0.85rem;color:#52525b;">
            Upload your news broadcast. Supported: MP4, MKV, AVI, MOV, WebM.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Styled upload drop zone placeholder shown before upload
    uploaded_file = st.file_uploader(
        "Upload video file",
        type=["mp4", "mkv", "avi", "mov", "webm"],
        label_visibility="collapsed",
        key="video_upload",
    )

    if uploaded_file is None and not st.session_state.pipeline_complete:
        st.markdown("""
        <div style="
            background: #0a0a0a;
            border: 2px dashed #2a1a4e;
            border-radius: 16px;
            padding: 3.5rem 2rem;
            text-align: center;
            margin: 0.5rem 0 2rem 0;
            transition: border-color 0.2s;
        ">
            <div style="margin-bottom:1.25rem;">
                <div style="
                    width:56px;height:56px;
                    background:linear-gradient(135deg,rgba(124,58,237,0.2),rgba(79,70,229,0.2));
                    border:1px solid rgba(124,58,237,0.3);
                    border-radius:14px;
                    display:inline-flex;align-items:center;justify-content:center;
                ">
                    <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                         stroke="#a78bfa" stroke-width="1.8"
                         stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="23 7 16 12 23 17 23 7"/>
                        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                    </svg>
                </div>
            </div>
            <p style="margin:0 0 0.5rem 0;font-size:1rem;font-weight:600;color:#ffffff;">
                Drop your video file here
            </p>
            <p style="margin:0;font-size:0.82rem;color:#3f3f46;">
                Or click above to browse &mdash; MP4, MKV, AVI, MOV, WebM
            </p>
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file is not None:
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = str(temp_dir / uploaded_file.name)

        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(f"""
        <div style="
            display:flex;align-items:center;gap:14px;
            background:#0a0a0a;border:1px solid #1c1c1c;border-radius:10px;
            padding:0.85rem 1.25rem;margin:0.75rem 0 1.5rem 0;
        ">
            <div style="
                width:36px;height:36px;
                background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.3);
                border-radius:8px;display:flex;align-items:center;justify-content:center;
                flex-shrink:0;
            ">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a78bfa"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"/>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
            </div>
            <div style="flex:1;">
                <p style="margin:0;font-size:0.88rem;font-weight:600;color:#ffffff;">{uploaded_file.name}</p>
                <p style="margin:0;font-size:0.75rem;color:#52525b;margin-top:2px;">{file_size_mb:.2f} MB &middot; Ready to process</p>
            </div>
            <div style="
                background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.35);
                color:#10b981;font-size:0.7rem;font-weight:600;
                padding:3px 10px;border-radius:999px;letter-spacing:0.05em;
            ">READY</div>
        </div>
        """, unsafe_allow_html=True)

        col_run, col_reset, _ = st.columns([1.5, 1.2, 4])

        with col_run:
            run_disabled = st.session_state.pipeline_running
            if st.button(
                "Run Pipeline  →",
                key="btn_run",
                disabled=run_disabled,
                use_container_width=True,
            ):
                st.session_state.pipeline_running = True
                st.session_state.pipeline_complete = False
                st.session_state.transcript = None
                st.session_state.clusters = None
                st.session_state.metrics = None
                st.session_state.summaries = None
                st.session_state.tts_paths = None
                st.session_state.agent1_events = []
                st.session_state.log_messages = []
                st.session_state.feedback_prefs = {}
                for stage in st.session_state.stage_statuses:
                    st.session_state.stage_statuses[stage] = "pending"
                st.rerun()

        with col_reset:
            if st.button("Reset", key="btn_reset", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        if st.session_state.pipeline_running:
            feedback = st.session_state.get("feedback_prefs", {}) or None
            run_pipeline_with_ui(video_path, feedback=feedback)

    # Results and feedback
    render_results_panel()
    render_feedback_panel()


def main():
    init_session_state()

    if st.session_state.current_page == "landing":
        # Hide sidebar on landing page
        st.markdown("""
        <style>
            section[data-testid="stSidebar"] { display: none !important; }
            .block-container { padding-left: 0 !important; padding-right: 0 !important; }
        </style>
        """, unsafe_allow_html=True)
        render_landing_page()
    else:
        render_app_page()


if __name__ == "__main__":
    main()

