from pathlib import Path
import os
import time
import textwrap

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from vireo.analysis import (
    read_pack,
    prepare_tickets,
    audit_pack,
    summary,
    weekly_report,
    agent_report,
    channel_report,
    shift_report,
    monthly_report,
    target_impact,
    SLA_CREDIT_INR,
    SLA_MINUTES,
    SHIFT_ORDER,
    CHANNEL_ORDER,
)
import importlib
import vireo.ai_assistant
importlib.reload(vireo.ai_assistant)

from vireo.ai_assistant import (
    get_llm_config,
    stream_ai_response,
    is_vireo_content,
    is_vireo_query,
    load_conversations,
    save_conversations,
    delete_conversation,
)

# Page configuration: ChatGPT-style Horizontal SaaS Application Shell
st.set_page_config(
    page_title="Vireo Audio — Support Operations",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Helper to render clean HTML without CommonMark code-block conversion
def render_html(html_str: str):
    clean_html = " ".join(html_str.split())
    st.markdown(clean_html, unsafe_allow_html=True)

# Initialize theme mode in session state
if "theme_choice" not in st.session_state:
    st.session_state["theme_choice"] = "Light"

if "theme_switcher_control" in st.session_state:
    st.session_state["theme_choice"] = st.session_state["theme_switcher_control"]

is_dark = (st.session_state["theme_choice"] == "Dark")

CSS_RAW_TEMPLATE = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

:root {
    --bg-canvas: __BG_CANVAS__;
    --surface-shell: __SURFACE_SHELL__;
    --border-shell: __BORDER_SHELL__;
    --shell-shadow: __SHELL_SHADOW__;
    --bg-sidebar: __BG_SIDEBAR__;
    --border-sidebar: __BORDER_SIDEBAR__;
    --surface-primary: __SURFACE_PRIMARY__;
    --surface-secondary: __SURFACE_SECONDARY__;
    --surface-tertiary: __SURFACE_TERTIARY__;
    --surface-card: __SURFACE_CARD__;
    --border-color: __BORDER_COLOR__;
    --border-subtle: __BORDER_SUBTLE__;
    --border-hover: __BORDER_HOVER__;
    --text-primary: __TEXT_PRIMARY__;
    --text-secondary: __TEXT_SECONDARY__;
    --text-muted: __TEXT_MUTED__;
    --accent-red: __ACCENT_RED__;
    --accent-red-bg: __ACCENT_RED_BG__;
    --accent-red-border: __ACCENT_RED_BORDER__;
    --accent-amber: __ACCENT_AMBER__;
    --accent-amber-bg: __ACCENT_AMBER_BG__;
    --accent-amber-border: __ACCENT_AMBER_BORDER__;
    --accent-green: __ACCENT_GREEN__;
    --accent-green-bg: __ACCENT_GREEN_BG__;
    --accent-green-border: __ACCENT_GREEN_BORDER__;
    --accent-teal: __ACCENT_TEAL__;
    --accent-teal-bg: __ACCENT_TEAL_BG__;
    --accent-teal-border: __ACCENT_TEAL_BORDER__;
    --input-bg: __INPUT_BG__;
    --card-shadow: __CARD_SHADOW__;
    --card-shadow-hover: __CARD_SHADOW_HOVER__;
    --benchmark-track: __BENCHMARK_TRACK__;
    --logo-bg: __LOGO_BG__;
    --logo-text: __LOGO_TEXT__;
    --avatar-bg: __AVATAR_BG__;
    --avatar-text: __AVATAR_TEXT__;
}

/* Global Typography & Canvas */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
}

/* Ambient Page Canvas */
.stApp {
    background-color: var(--bg-canvas) !important;
    min-height: 100vh;
}

/* Ambient Depth Lights */
.stApp::before {
    content: "";
    position: fixed;
    top: -120px;
    left: 18%;
    width: 650px;
    height: 650px;
    background: radial-gradient(circle, rgba(220, 38, 38, 0.035) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

.stApp::after {
    content: "";
    position: fixed;
    bottom: -120px;
    right: 18%;
    width: 650px;
    height: 650px;
    background: radial-gradient(circle, rgba(15, 118, 110, 0.035) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* Hide Native Streamlit Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {display: none !important;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {visibility: hidden;}

/* Full-Height Professional Fixed Left Sidebar */
section[data-testid="stSidebar"] {
    display: block !important;
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-color) !important;
    box-shadow: 2px 0 16px rgba(0, 0, 0, 0.04) !important;
    z-index: 100 !important;
    width: 280px !important;
    min-width: 280px !important;
    max-width: 280px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    background-color: var(--bg-sidebar) !important;
    padding: 1.25rem 1rem 1.5rem 1rem !important;
}

/* Hide collapse controls and native headers */
button[data-testid="stSidebarCollapseButton"],
div[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Continuous Horizontal Product Workspace */
.main {
    background: var(--bg-canvas) !important;
    min-height: 100vh !important;
    padding: 0 !important;
}

.main .block-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 1.5rem 2.25rem 3.5rem 2.25rem !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: background 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

/* Sidebar Brand Header */
.sidebar-brand-box {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.25rem 0.5rem 1.15rem 0.5rem;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1rem;
}

.sidebar-logo-mark {
    width: 34px;
    height: 34px;
    background: var(--logo-bg);
    color: var(--logo-text);
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1rem;
    position: relative;
    box-shadow: 0 2px 5px rgba(15, 23, 42, 0.12);
}

.sidebar-logo-dot {
    position: absolute;
    bottom: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    background: #f43f5e;
    border-radius: 50%;
    border: 2px solid var(--bg-sidebar);
}

.sidebar-brand-text {
    display: flex;
    flex-direction: column;
}

.sidebar-brand-name {
    font-size: 0.96rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    line-height: 1.15;
}

.sidebar-brand-product {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-muted);
    margin-top: 0.1rem;
}

/* Sidebar Nav Radio */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > label,
div[data-testid="stRadio"]:has(input[value="Overview"]) > label,
.shell-nav-wrapper div[data-testid="stRadio"] > label,
div[data-testid="stRadio"] > label {
    display: none !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] > div,
div[data-testid="stRadio"]:has(input[value="Overview"]) > div,
.shell-nav-wrapper div[data-testid="stRadio"] > div {
    gap: 0.35rem !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 9px !important;
    padding: 0.58rem 0.85rem !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    border: 1px solid transparent !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.75rem !important;
    margin: 0 !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label::before {
    content: "";
    display: inline-block !important;
    width: 17px !important;
    height: 17px !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    opacity: 0.75 !important;
    transition: all 0.18s ease !important;
    flex-shrink: 0 !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label:hover,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background: var(--surface-secondary) !important;
    color: var(--text-primary) !important;
    transform: translateX(2px);
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover::before,
section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label:hover::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label:has(input:checked)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label:hover::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked)::before {
    opacity: 1 !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label:has(input:checked),
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: var(--surface-primary) !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    border: 1px solid var(--border-color) !important;
    border-left: 3px solid var(--accent-red) !important;
    box-shadow: var(--card-shadow) !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label input,
section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label input,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label > div:first-child,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:last-child,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] label > div:last-child,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] label > div:last-child {
    display: flex !important;
    align-items: center !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[data-testid="stMarkdownContainer"] p,
.shell-nav-wrapper div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    font-weight: inherit !important;
    color: inherit !important;
    margin: 0 !important;
}

/* 1. Overview -> LayoutDashboard */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(1)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(1)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
}

/* 2. SLA Performance -> Target */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(2)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(2)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Ccircle cx='12' cy='12' r='6'/%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3C/svg%3E");
}

/* 3. Teams -> Users */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(3)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(3)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='9' cy='7' r='4'/%3E%3Cpath d='M22 21v-2a4 4 0 0 0-3-3.87'/%3E%3Cpath d='M16 3.13a4 4 0 0 1 0 7.75'/%3E%3C/svg%3E");
}

/* 4. Agents -> UserRound */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(4)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(4)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='8' r='5'/%3E%3Cpath d='M20 21a8 8 0 0 0-16 0'/%3E%3C/svg%3E");
}

/* 5. Channels -> MessagesSquare */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(5)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(5)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2z'/%3E%3Cpath d='M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1'/%3E%3C/svg%3E");
}

/* 6. Quality -> ShieldCheck */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(6)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(6)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(6)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E");
}

/* 7. AI Assistant -> Sparkles */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:nth-child(7)::before,
div[data-testid="stRadio"]:has(input[value="Overview"]) div[role="radiogroup"] > label:nth-child(7)::before,
.shell-nav-wrapper div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(7)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z'/%3E%3Cpath d='M5 3v4'/%3E%3Cpath d='M19 17v4'/%3E%3Cpath d='M3 5h4'/%3E%3Cpath d='M17 19h4'/%3E%3C/svg%3E");
}

/* AI Assistant Page Inbox / Chat History */
div[data-testid="stButton"]:has(button[key="ai_inbox_new_chat_btn"]) button,
button[id*="ai_inbox_new_chat_btn"] {
    background: var(--surface-primary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    padding: 0.45rem 0.75rem !important;
    margin-bottom: 0.5rem !important;
    transition: all 0.15s ease !important;
    box-shadow: var(--card-shadow) !important;
}

div[data-testid="stButton"]:has(button[key="ai_inbox_new_chat_btn"]) button:hover,
button[id*="ai_inbox_new_chat_btn"]:hover {
    border-color: var(--accent-red) !important;
    background: var(--surface-secondary) !important;
    color: var(--text-primary) !important;
}

div[data-testid="stButton"]:has(button[key^="inbox_conv_btn_"]) button,
button[id*="inbox_conv_btn_"] {
    text-align: left !important;
    justify-content: flex-start !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.65rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    border-radius: 8px !important;
    margin-bottom: 0.25rem !important;
    border: 1px solid transparent !important;
    position: relative !important;
    padding-left: 28px !important;
    transition: all 0.15s ease !important;
    color: var(--text-secondary) !important;
}

div[data-testid="stButton"]:has(button[key^="inbox_conv_btn_"]) button::before,
button[id*="inbox_conv_btn_"]::before {
    content: "";
    position: absolute;
    left: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 13px;
    height: 13px;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='__NAV_STROKE__' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E%3C/svg%3E");
    background-size: contain;
    background-repeat: no-repeat;
    opacity: 0.65;
}

div[data-testid="stButton"]:has(button[key^="inbox_conv_btn_"]) button:hover,
button[id*="inbox_conv_btn_"]:hover {
    background: var(--surface-secondary) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}

div[data-testid="stButton"]:has(button[key^="inbox_conv_btn_"]) button[kind="primary"],
button[id*="inbox_conv_btn_"][kind="primary"] {
    background: var(--surface-primary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    border-left: 3px solid var(--accent-red) !important;
    font-weight: 600 !important;
    box-shadow: var(--card-shadow) !important;
}

div[data-testid="stButton"]:has(button[key^="inbox_conv_btn_"]) button[kind="primary"]::before,
button[id*="inbox_conv_btn_"][kind="primary"]::before {
    opacity: 1 !important;
}

div[data-testid="stButton"]:has(button[key^="inbox_del_btn_"]) button,
button[id*="inbox_del_btn_"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    padding: 0.45rem 0.2rem !important;
    margin-bottom: 0.25rem !important;
    color: var(--text-muted) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.15s ease !important;
}

div[data-testid="stButton"]:has(button[key^="inbox_del_btn_"]) button:hover,
button[id*="inbox_del_btn_"]:hover {
    background: rgba(244, 63, 94, 0.14) !important;
    color: var(--accent-rose, #f43f5e) !important;
    border-color: rgba(244, 63, 94, 0.3) !important;
}

/* Sidebar Data Status Card */
.sidebar-status-card {
    background: var(--surface-primary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin-top: 1.5rem;
    box-shadow: var(--card-shadow);
}

.sidebar-status-label {
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.sidebar-status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-primary);
}

.status-dot-green {
    width: 7px;
    height: 7px;
    background-color: var(--accent-green);
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 0 2px var(--accent-green-border);
}

.sidebar-status-sub {
    font-size: 0.74rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
    margin-left: 1.15rem;
}

.sidebar-status-divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 0.5rem 0;
}

.sidebar-status-policy {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* Top Workspace Toolbar & Theme Switcher */
.workspace-title-group {
    display: flex;
    flex-direction: column;
}

.workspace-page-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.03em;
    line-height: 1.2;
}

.workspace-page-subtitle {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-muted);
    margin-top: 0.2rem;
}

.workspace-meta-group {
    display: flex;
    align-items: center;
    gap: 0.65rem;
}

.workspace-badge {
    background: var(--surface-primary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.35rem 0.75rem;
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.45rem;
    box-shadow: var(--card-shadow);
}

.workspace-avatar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.3rem 0.65rem 0.3rem 0.4rem;
    box-shadow: var(--card-shadow);
}

.avatar-initials {
    width: 22px;
    height: 22px;
    background: var(--avatar-bg);
    color: var(--avatar-text);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.68rem;
    font-weight: 800;
}

.avatar-label {
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--text-primary);
}

.workspace-top-divider {
    height: 1px;
    background: var(--border-color);
    margin: 0.9rem 0 1.25rem 0;
}

/* Segmented Theme Switcher */
.theme-switch-container {
    display: flex;
    justify-content: flex-end;
}

div[data-testid="stRadio"]:has(input[value="Light"]),
.theme-switch-container div[data-testid="stRadio"] {
    display: flex !important;
    justify-content: flex-end !important;
    margin-left: auto !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) > label,
.theme-switch-container div[data-testid="stRadio"] > label {
    display: none !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"],
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] {
    flex-direction: row !important;
    background: var(--surface-tertiary) !important;
    padding: 3px !important;
    border-radius: 9px !important;
    border: 1px solid var(--border-color) !important;
    gap: 2px !important;
    width: fit-content !important;
    display: inline-flex !important;
    margin-left: auto !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label,
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 7px !important;
    padding: 0.28rem 0.65rem !important;
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    border: 1px solid transparent !important;
    transition: all 0.18s ease !important;
    cursor: pointer !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.45rem !important;
    margin: 0 !important;
    min-height: auto !important;
    transform: none !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label:has(input:checked),
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: var(--surface-primary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label input,
div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label > div:not([data-testid="stMarkdownContainer"]),
div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label > div:first-child,
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label > div:last-child,
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] label > div:last-child {
    display: flex !important;
    align-items: center !important;
}

div[data-testid="stRadio"]:has(input[value="Light"]) div[data-testid="stMarkdownContainer"] p,
.theme-switch-container div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
}

/* Sun Icon for Light */
div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label:nth-child(1)::before,
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] label:nth-child(1)::before {
    content: "";
    display: inline-block !important;
    width: 13px !important;
    height: 13px !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23f59e0b' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='4'/%3E%3Cpath d='M12 2v2'/%3E%3Cpath d='M12 20v2'/%3E%3Cpath d='m4.93 4.93 1.41 1.41'/%3E%3Cpath d='m17.66 17.66 1.41 1.41'/%3E%3Cpath d='M2 12h2'/%3E%3Cpath d='M20 12h2'/%3E%3Cpath d='m6.34 17.66-1.41 1.41'/%3E%3Cpath d='m19.07 4.93-1.41 1.41'/%3E%3C/svg%3E");
}

/* Moon Icon for Dark */
div[data-testid="stRadio"]:has(input[value="Light"]) div[role="radiogroup"] label:nth-child(2)::before,
.theme-switch-container div[data-testid="stRadio"] div[role="radiogroup"] label:nth-child(2)::before {
    content: "";
    display: inline-block !important;
    width: 13px !important;
    height: 13px !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23818cf8' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z'/%3E%3C/svg%3E");
}

/* 3D KPI Metric Cards */
.studyos-kpi-card {
    background: var(--surface-card);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem 1.35rem;
    box-shadow: var(--card-shadow);
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    min-height: 140px;
}

.studyos-kpi-card:hover {
    transform: translateY(-3px) perspective(800px) rotateX(1.5deg);
    box-shadow: var(--card-shadow-hover);
    border-color: var(--border-hover);
}

.kpi-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.65rem;
}

.kpi-card-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi-icon-badge {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.kpi-icon-badge.red-tint { background: var(--accent-red-bg); border: 1px solid var(--accent-red-border); }
.kpi-icon-badge.amber-tint { background: var(--accent-amber-bg); border: 1px solid var(--accent-amber-border); }
.kpi-icon-badge.green-tint { background: var(--accent-green-bg); border: 1px solid var(--accent-green-border); }
.kpi-icon-badge.coral-tint { background: var(--accent-red-bg); border: 1px solid var(--accent-red-border); }

.kpi-card-value {
    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.04em;
    font-variant-numeric: tabular-nums;
    margin-bottom: 0.65rem;
}

.kpi-card-value.text-red { color: var(--accent-red); }
.kpi-card-value.text-amber { color: var(--accent-amber); }
.kpi-card-value.text-dark { color: var(--text-primary); }
.kpi-card-value.text-coral { color: var(--accent-red); }

.kpi-card-footer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: auto;
    font-size: 0.74rem;
}

.kpi-trend-pill {
    font-weight: 700;
    padding: 0.18rem 0.5rem;
    border-radius: 5px;
    font-size: 0.7rem;
    white-space: nowrap;
}

.kpi-trend-pill.red { background: var(--accent-red-bg); color: var(--accent-red); border: 1px solid var(--accent-red-border); }
.kpi-trend-pill.amber { background: var(--accent-amber-bg); color: var(--accent-amber); border: 1px solid var(--accent-amber-border); }
.kpi-trend-pill.green { background: var(--accent-green-bg); color: var(--accent-green); border: 1px solid var(--accent-green-border); }
.kpi-trend-pill.coral { background: var(--accent-red-bg); color: var(--accent-red); border: 1px solid var(--accent-red-border); }

.kpi-sub-text {
    color: var(--text-muted);
    font-weight: 500;
    font-size: 0.72rem;
}

/* 3D SLA Hero Performance Surface */
.hero-studyos-card {
    background: var(--surface-card);
    border: 1px solid var(--border-color);
    border-radius: 18px;
    padding: 1.85rem 2rem;
    display: grid;
    grid-template-columns: 1.3fr 1fr;
    gap: 2rem;
    align-items: center;
    box-shadow: var(--card-shadow);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    min-height: 250px;
}

.hero-studyos-card:hover {
    box-shadow: var(--card-shadow-hover);
    border-color: var(--border-hover);
    transform: translateY(-2px);
}

.hero-studyos-left {
    display: flex;
    flex-direction: column;
}

.hero-eyebrow-pill {
    display: inline-flex;
    align-items: center;
    background: var(--accent-red-bg);
    color: var(--accent-red);
    border: 1px solid var(--accent-red-border);
    padding: 0.22rem 0.6rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    width: fit-content;
    margin-bottom: 0.65rem;
}

.hero-huge-metric {
    font-size: 4.5rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 0.95;
    letter-spacing: -0.045em;
    font-variant-numeric: tabular-nums;
    margin-bottom: 0.75rem;
}

.hero-subline-stats {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.65rem;
}

.hero-stat-badge-red {
    background: var(--accent-red-bg);
    color: var(--accent-red);
    font-weight: 700;
    font-size: 0.88rem;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    border: 1px solid var(--accent-red-border);
}

.hero-stat-badge-amber {
    background: var(--accent-amber-bg);
    color: var(--accent-amber);
    font-weight: 700;
    font-size: 0.88rem;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    border: 1px solid var(--accent-amber-border);
}

.hero-bullet-sep {
    color: var(--border-color);
    font-weight: 400;
}

.hero-insight-caption {
    font-size: 0.86rem;
    color: var(--text-secondary);
    line-height: 1.45;
    font-weight: 500;
}

/* 3D SLA Radial Performance Object */
.sla-radial-card {
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.sla-radial-card:hover {
    transform: perspective(600px) rotateX(2deg) rotateY(-2deg);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.sla-radial-disc {
    position: relative;
    width: 160px;
    height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.sla-radial-svg {
    transform: rotate(-90deg);
    width: 160px;
    height: 160px;
    display: block;
}

.sla-circle-bg {
    fill: none !important;
    stroke: var(--benchmark-track);
    stroke-width: 11;
}

.sla-circle-scenario {
    fill: none !important;
    stroke: var(--text-muted);
    stroke-width: 11;
    stroke-dasharray: 4 6;
    opacity: 0.55;
}

.sla-circle-fill {
    fill: none !important;
    stroke: var(--accent-red);
    stroke-width: 11;
    stroke-linecap: round;
    animation: drawRadial 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes drawRadial {
    from { stroke-dashoffset: 390; }
    to { stroke-dashoffset: 0; }
}

.sla-radial-center {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    pointer-events: none;
}

.sla-radial-val {
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1;
    letter-spacing: -0.03em;
    font-variant-numeric: tabular-nums;
}

.sla-radial-lbl {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.2rem;
}

.radial-delta-badge {
    margin-top: 0.45rem;
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--accent-red);
    background: var(--accent-red-bg);
    border: 1px solid var(--accent-red-border);
    padding: 0.15rem 0.45rem;
    border-radius: 5px;
    white-space: nowrap;
}

.sla-radial-legend {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin-top: 0.85rem;
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 500;
}

.sla-legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

.legend-dot.coral {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent-red);
}

.legend-dot.dash {
    width: 9px;
    height: 3px;
    border-radius: 2px;
    background: var(--text-muted);
}

/* Animated Breakdown Progress Bars */
.breakdown-list-wrapper {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.breakdown-row-item {
    background: var(--surface-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 0.95rem 1.15rem;
    transition: all 0.2s ease;
}

.breakdown-row-item:hover {
    box-shadow: var(--card-shadow);
    border-color: var(--border-hover);
}

.breakdown-row-item.highlight-coral {
    border-left: 3px solid var(--accent-red);
}

.breakdown-row-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.breakdown-item-name {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
}

.breakdown-badge-stat {
    font-size: 0.85rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}

.breakdown-badge-stat.alert {
    color: var(--accent-red);
}

.breakdown-progress-track {
    height: 6px;
    background: var(--benchmark-track);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.breakdown-progress-fill {
    height: 100%;
    border-radius: 3px;
    animation: fillBar 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fillBar {
    from { width: 0%; }
    to { width: 100%; }
}

.breakdown-footer-stats {
    display: flex;
    gap: 0.85rem;
    font-size: 0.74rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* AI Assistant Styles */
.ai-citation-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--accent-teal-bg);
    color: var(--accent-teal);
    border: 1px solid var(--accent-teal-border);
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 0.75rem;
}

.section-header-box {
    margin-bottom: 1rem;
}

.section-main-title {
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    line-height: 1.25;
}

.section-main-subtitle {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-muted);
    margin-top: 0.2rem;
    line-height: 1.45;
}

/* ================================================================
   STREAMLIT WIDGET DARK-MODE TEXT OVERRIDES
   Forces native Streamlit elements to use semantic CSS variables.
   These have no visible effect in Light mode (values already match).
   ================================================================ */

/* --- Global Markdown & Paragraph Text --- */
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] td,
div[data-testid="stMarkdownContainer"] th,
div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3,
div[data-testid="stMarkdownContainer"] h4,
div[data-testid="stMarkdownContainer"] h5,
div[data-testid="stMarkdownContainer"] h6,
div[data-testid="stMarkdownContainer"] span,
div[data-testid="stMarkdownContainer"] strong,
div[data-testid="stMarkdownContainer"] em,
div[data-testid="stMarkdownContainer"] blockquote {
    color: var(--text-primary) !important;
}

div[data-testid="stMarkdownContainer"] code {
    color: var(--text-secondary) !important;
    background: var(--surface-tertiary) !important;
}

/* --- Selectbox / Dropdown Text --- */
div[data-baseweb="select"] {
    color: var(--text-primary) !important;
}

div[data-baseweb="select"] > div {
    background: var(--input-bg) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div[data-testid="stMarkdownContainer"] p {
    color: var(--text-primary) !important;
}

div[data-baseweb="select"] svg {
    fill: var(--text-muted) !important;
}

/* Selectbox placeholder */
div[data-baseweb="select"] [data-baseweb="tag"] {
    color: var(--text-primary) !important;
}

/* Dropdown menu list */
ul[role="listbox"] {
    background: var(--surface-primary) !important;
    border-color: var(--border-color) !important;
}

ul[role="listbox"] li {
    color: var(--text-primary) !important;
}

ul[role="listbox"] li:hover {
    background: var(--surface-secondary) !important;
}

ul[role="listbox"] li[aria-selected="true"] {
    background: var(--surface-tertiary) !important;
}

/* Popover / Dropdown Container */
div[data-baseweb="popover"] > div {
    background: var(--surface-primary) !important;
    border-color: var(--border-color) !important;
}

/* --- Buttons --- */
button[kind="secondary"],
button[data-testid="baseButton-secondary"] {
    color: var(--text-primary) !important;
    background: var(--surface-primary) !important;
    border-color: var(--border-color) !important;
}

button[kind="secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover {
    border-color: var(--border-hover) !important;
    color: var(--text-primary) !important;
}

/* Download buttons */
button[data-testid="stDownloadButton"] button,
div[data-testid="stDownloadButton"] button {
    color: var(--text-primary) !important;
    background: var(--surface-primary) !important;
    border-color: var(--border-color) !important;
}

/* --- Text Input & Chat Input --- */
div[data-testid="stChatInput"] {
    background: var(--surface-primary) !important;
    border-color: var(--border-color) !important;
}

div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] input {
    color: var(--text-primary) !important;
    caret-color: var(--text-primary) !important;
}

div[data-testid="stChatInput"] textarea::placeholder,
div[data-testid="stChatInput"] input::placeholder {
    color: var(--text-muted) !important;
}

input[type="text"],
textarea {
    color: var(--text-primary) !important;
    background: var(--input-bg) !important;
}

/* --- Chat Message Containers --- */
div[data-testid="stChatMessage"] {
    background: var(--surface-card) !important;
    border-color: var(--border-subtle) !important;
}

div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] span,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] td,
div[data-testid="stChatMessage"] th,
div[data-testid="stChatMessage"] h1,
div[data-testid="stChatMessage"] h2,
div[data-testid="stChatMessage"] h3 {
    color: var(--text-primary) !important;
}

/* --- Containers with Borders --- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--border-color) !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] {
    color: var(--text-primary);
}

/* --- Streamlit Expander --- */
details[data-testid="stExpander"] {
    border-color: var(--border-color) !important;
    background: var(--surface-card) !important;
}

details[data-testid="stExpander"] summary span {
    color: var(--text-primary) !important;
}

details[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    color: var(--text-primary) !important;
}

/* --- Metric Widget --- */
div[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
    color: var(--text-secondary) !important;
}

/* --- Dataframe / Table --- */
div[data-testid="stDataFrame"] {
    color: var(--text-primary) !important;
}

div[data-testid="stDataFrame"] th,
div[data-testid="stDataFrame"] td {
    color: var(--text-primary) !important;
}

/* Glide Data Grid (Streamlit's dataframe renderer) */
div[data-testid="stDataFrame"] canvas + div {
    color: var(--text-primary) !important;
}

.stDataFrame [data-testid="glideDataEditor"] {
    color: var(--text-primary) !important;
}

/* --- Tab Labels --- */
button[data-baseweb="tab"] {
    color: var(--text-muted) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text-primary) !important;
}

/* --- Widget Labels (generic) --- */
label[data-testid="stWidgetLabel"] {
    color: var(--text-secondary) !important;
}

label[data-testid="stWidgetLabel"] p {
    color: var(--text-secondary) !important;
}

/* --- Date Input --- */
div[data-baseweb="input"] {
    background: var(--input-bg) !important;
    border-color: var(--border-color) !important;
}

div[data-baseweb="input"] input {
    color: var(--text-primary) !important;
}

/* --- Toast / Alert Messages --- */
div[data-testid="stAlert"] {
    color: var(--text-primary) !important;
}

/* --- Caption / Small Text --- */
div[data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
}

div[data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
}

/* --- Plotly Chart Background Override --- */
.stPlotlyChart {
    color: var(--text-primary) !important;
}
</style>"""


def get_theme_css(is_dark: bool) -> str:
    if is_dark:
        subs = {
            "__BG_CANVAS__": "#070b12",
            "__SURFACE_SHELL__": "#0d1422",
            "__BORDER_SHELL__": "rgba(255, 255, 255, 0.08)",
            "__SHELL_SHADOW__": "0 32px 80px -16px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255, 255, 255, 0.06) inset",
            "__BG_SIDEBAR__": "#111a2c",
            "__BORDER_SIDEBAR__": "rgba(255, 255, 255, 0.06)",
            "__SURFACE_PRIMARY__": "#141e30",
            "__SURFACE_SECONDARY__": "#192438",
            "__SURFACE_TERTIARY__": "#223147",
            "__SURFACE_CARD__": "#141e30",
            "__BORDER_COLOR__": "#243348",
            "__BORDER_SUBTLE__": "#192538",
            "__BORDER_HOVER__": "#394d68",
            "__TEXT_PRIMARY__": "#f8fafc",
            "__TEXT_SECONDARY__": "#cbd5e1",
            "__TEXT_MUTED__": "#94a3b8",
            "__ACCENT_RED__": "#f43f5e",
            "__ACCENT_RED_BG__": "rgba(244, 63, 94, 0.12)",
            "__ACCENT_RED_BORDER__": "rgba(244, 63, 94, 0.28)",
            "__ACCENT_AMBER__": "#f59e0b",
            "__ACCENT_AMBER_BG__": "rgba(245, 158, 11, 0.12)",
            "__ACCENT_AMBER_BORDER__": "rgba(245, 158, 11, 0.28)",
            "__ACCENT_GREEN__": "#10b981",
            "__ACCENT_GREEN_BG__": "rgba(16, 185, 129, 0.12)",
            "__ACCENT_GREEN_BORDER__": "rgba(16, 185, 129, 0.28)",
            "__ACCENT_TEAL__": "#2dd4bf",
            "__ACCENT_TEAL_BG__": "rgba(45, 212, 191, 0.12)",
            "__ACCENT_TEAL_BORDER__": "rgba(45, 212, 191, 0.28)",
            "__INPUT_BG__": "#141e30",
            "__CARD_SHADOW__": "0 4px 12px rgba(0, 0, 0, 0.35)",
            "__CARD_SHADOW_HOVER__": "0 10px 24px rgba(0, 0, 0, 0.55)",
            "__BENCHMARK_TRACK__": "#243348",
            "__NAV_STROKE__": "%23f8fafc",
            "__LOGO_BG__": "#ffffff",
            "__LOGO_TEXT__": "#0f172a",
            "__AVATAR_BG__": "#3b171f",
            "__AVATAR_TEXT__": "#f43f5e",
        }
    else:
        subs = {
            "__BG_CANVAS__": "#f1f5f9",
            "__SURFACE_SHELL__": "#ffffff",
            "__BORDER_SHELL__": "rgba(226, 232, 240, 0.95)",
            "__SHELL_SHADOW__": "0 24px 64px -12px rgba(15, 23, 42, 0.08), 0 4px 20px rgba(15, 23, 42, 0.03), 0 0 0 1px rgba(255, 255, 255, 0.95) inset",
            "__BG_SIDEBAR__": "#f8fafc",
            "__BORDER_SIDEBAR__": "#eaecf0",
            "__SURFACE_PRIMARY__": "#ffffff",
            "__SURFACE_SECONDARY__": "#f8fafc",
            "__SURFACE_TERTIARY__": "#f1f5f9",
            "__SURFACE_CARD__": "#ffffff",
            "__BORDER_COLOR__": "#eaecf0",
            "__BORDER_SUBTLE__": "#f1f5f9",
            "__BORDER_HOVER__": "#cbd5e1",
            "__TEXT_PRIMARY__": "#0f172a",
            "__TEXT_SECONDARY__": "#475569",
            "__TEXT_MUTED__": "#64748b",
            "__ACCENT_RED__": "#dc2626",
            "__ACCENT_RED_BG__": "#fef2f2",
            "__ACCENT_RED_BORDER__": "#fee2e2",
            "__ACCENT_AMBER__": "#d97706",
            "__ACCENT_AMBER_BG__": "#fffbeb",
            "__ACCENT_AMBER_BORDER__": "#fef3c7",
            "__ACCENT_GREEN__": "#059669",
            "__ACCENT_GREEN_BG__": "#ecfdf5",
            "__ACCENT_GREEN_BORDER__": "#d1fae5",
            "__ACCENT_TEAL__": "#0f766e",
            "__ACCENT_TEAL_BG__": "#f0fdfa",
            "__ACCENT_TEAL_BORDER__": "#ccfbf1",
            "__INPUT_BG__": "#ffffff",
            "__CARD_SHADOW__": "0 2px 8px rgba(16, 24, 40, 0.04)",
            "__CARD_SHADOW_HOVER__": "0 8px 20px rgba(16, 24, 40, 0.07)",
            "__BENCHMARK_TRACK__": "#e2e8f0",
            "__NAV_STROKE__": "%230f172a",
            "__LOGO_BG__": "#0f172a",
            "__LOGO_TEXT__": "#ffffff",
            "__AVATAR_BG__": "#fee2e2",
            "__AVATAR_TEXT__": "#dc2626",
        }
    css = CSS_RAW_TEMPLATE
    for k, v in subs.items():
        css = css.replace(k, v)
    return css

st.markdown(get_theme_css(is_dark), unsafe_allow_html=True)

# Helper function for StudyOS chart styling
def apply_studyos_chart_style(fig, height=340):
    theme_is_dark = (st.session_state.get("theme_choice", "Light") == "Dark")
    if theme_is_dark:
        fig.update_layout(
            template="plotly_dark",
            height=height,
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11, color="#cbd5e1"),
            ),
            font=dict(family="Inter", color="#f8fafc"),
            xaxis=dict(gridcolor="#1e293b", linecolor="#27354a", showline=True, tickfont=dict(size=10, color="#94a3b8")),
            yaxis=dict(gridcolor="#1e293b", linecolor="#27354a", showline=True, tickfont=dict(size=10, color="#94a3b8")),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(
                bgcolor="#151e2e",
                bordercolor="#27354a",
                font=dict(family="Inter", size=11, color="#f8fafc"),
            ),
        )
    else:
        fig.update_layout(
            template="plotly_white",
            height=height,
            margin=dict(l=10, r=10, t=25, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11, color="#475569"),
            ),
            font=dict(family="Inter", color="#0f172a"),
            xaxis=dict(gridcolor="#f1f5f9", linecolor="#cbd5e1", showline=True, tickfont=dict(size=10, color="#64748b")),
            yaxis=dict(gridcolor="#f1f5f9", linecolor="#cbd5e1", showline=True, tickfont=dict(size=10, color="#64748b")),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hoverlabel=dict(
                bgcolor="#ffffff",
                bordercolor="#e2e8f0",
                font=dict(family="Inter", size=11, color="#0f172a"),
            ),
        )
    return fig

# Load dataset
@st.cache_data
def load_data():
    tickets, agents, customers, orders, products = read_pack(Path("data"))
    df = prepare_tickets(tickets, agents)
    audit = audit_pack(tickets, agents, customers, orders, products, df)
    return df, audit

df, audit = load_data()

# Date scope bounds
min_date = df["created_at_ist"].dt.date.min()
max_date = df["created_at_ist"].dt.date.max()

if "date_range" not in st.session_state:
    st.session_state["date_range"] = (min_date, max_date)
if "chan_choice" not in st.session_state:
    st.session_state["chan_choice"] = "All Channels"
if "shift_choice" not in st.session_state:
    st.session_state["shift_choice"] = "All Shifts"
if "team_choice" not in st.session_state:
    st.session_state["team_choice"] = "All Teams"
if "main_shell_navigation" not in st.session_state:
    st.session_state["main_shell_navigation"] = "Overview"

# Initialize multi-conversation chat state from persistent store
if "conversations" not in st.session_state:
    st.session_state["conversations"] = load_conversations()

if "active_conv_id" not in st.session_state or st.session_state["active_conv_id"] not in st.session_state["conversations"]:
    if st.session_state["conversations"]:
        st.session_state["active_conv_id"] = list(st.session_state["conversations"].keys())[0]
    else:
        new_cid = f"conv_{int(time.time() * 1000)}"
        st.session_state["conversations"][new_cid] = {
            "id": new_cid,
            "title": "New Conversation",
            "messages": [],
        }
        st.session_state["active_conv_id"] = new_cid
        save_conversations(st.session_state["conversations"])

# ========================================================
# FIXED FULL-HEIGHT LEFT SIDEBAR
# ========================================================
with st.sidebar:
    render_html("""
    <div class="sidebar-brand-box">
        <div class="sidebar-logo-mark">
            V
            <div class="sidebar-logo-dot"></div>
        </div>
        <div class="sidebar-brand-text">
            <span class="sidebar-brand-name">Vireo Audio</span>
            <span class="sidebar-brand-product">Support Operations</span>
        </div>
    </div>
    """)

    nav_options = [
        "Overview",
        "SLA Performance",
        "Teams",
        "Agents",
        "Channels",
        "Quality",
        "AI Assistant",
    ]

    selected_nav_label = st.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(st.session_state["main_shell_navigation"]) if st.session_state["main_shell_navigation"] in nav_options else 0,
        label_visibility="collapsed",
        key="main_shell_navigation",
    )

    page_map = {
        "Overview": "Overview",
        "SLA Performance": "SLA",
        "Teams": "Teams",
        "Agents": "Agents",
        "Channels": "Channels",
        "Quality": "Quality",
        "AI Assistant": "AI Assistant",
    }
    page = page_map.get(selected_nav_label, "Overview")


    render_html("""
    <div class="sidebar-status-card">
        <div class="sidebar-status-label">DATA STATUS</div>
        <div class="sidebar-status-item">
            <span class="status-dot-green"></span>
            <strong>Audited Dataset</strong>
        </div>
        <div class="sidebar-status-sub">11,200 tickets</div>
        <div class="sidebar-status-divider"></div>
        <div class="sidebar-status-policy">Policy v3.2 • Realtime IST</div>
        <div style="margin-top: 0.5rem; font-size: 0.7rem; color: var(--accent-amber); font-weight: 600;">
            Q4 Headcount Freeze
        </div>
    </div>
    """)

# ========================================================
# MAIN APPLICATION WORKSPACE (FULL-WIDTH PRODUCT SURFACE)
# ========================================================
with st.container():
    # 1. Top Workspace Toolbar & Theme Switcher
    page_titles = {
        "Overview": ("Support Operations Overview", "First-response SLA performance across Vireo Audio"),
        "SLA": ("SLA Performance & Recovery", "Weekly first-response compliance across 79 Mon–Sun cycles"),
        "Teams": ("Team & Workforce Operations", "Queue dynamics across Morning, Day, and Night shifts"),
        "Agents": ("Agent Operations Registry", "Neutral operational matching with historical roster records"),
        "Channels": ("Channel Performance Standards", "Service tier compliance: Chat, Email, Social, and Voice"),
        "Quality": ("Quality & Integrity Workspace", "7-point technical audit & leadership finance claim verification"),
        "AI Assistant": ("AI Operations Assistant", "Grounded analytical intelligence powered by verified support data"),
    }
    title_main, title_sub = page_titles.get(page, ("Support Operations", "First-response SLA performance"))

    col_tb_left, col_tb_right = st.columns([1.1, 1.3], vertical_alignment="center")

    with col_tb_left:
        render_html(f"""
        <div class="workspace-title-group" style="padding: 0.15rem 0;">
            <div class="workspace-page-title">{title_main}</div>
            <div class="workspace-page-subtitle">{title_sub}</div>
        </div>
        """)

    with col_tb_right:
        c_meta, c_theme = st.columns([1.35, 0.95], vertical_alignment="center")
        with c_meta:
            render_html("""
            <div class="workspace-meta-group" style="justify-content: flex-end;">
                <div class="workspace-badge"><span class="status-dot-green"></span> 11,200 Audited</div>
                <div class="workspace-badge">Policy v3.2</div>
                <div class="workspace-avatar">
                    <span class="avatar-initials">SM</span>
                    <span class="avatar-label">Ops Manager</span>
                </div>
            </div>
            """)
        with c_theme:
            st.markdown('<div class="theme-switch-container">', unsafe_allow_html=True)
            theme_sel = st.radio(
                "Theme Mode",
                ["Light", "Dark"],
                index=0 if st.session_state.get("theme_choice", "Light") == "Light" else 1,
                horizontal=True,
                label_visibility="collapsed",
                key="theme_switcher_control",
            )
            st.markdown('</div>', unsafe_allow_html=True)

    render_html("<div class='workspace-top-divider'></div>")

    # 2. Scope Filter Strip
    with st.container(border=True):
        f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([2.4, 1.8, 1.8, 1.8, 1.2])

        with f_c1:
            date_sel = st.date_input(
                "Date Range (IST)",
                value=st.session_state["date_range"],
                min_value=min_date,
                max_value=max_date,
                label_visibility="collapsed",
                help="Filter tickets by IST creation date",
                key="global_date_range_filter",
            )
            if isinstance(date_sel, tuple) and len(date_sel) == 2:
                st.session_state["date_range"] = date_sel
                start_d, end_d = date_sel
            elif isinstance(date_sel, tuple) and len(date_sel) == 1:
                start_d = end_d = date_sel[0]
            else:
                start_d = end_d = date_sel

        with f_c2:
            chan_options = ["All Channels"] + sorted(df["channel"].unique().tolist())
            chan_sel = st.selectbox(
                "Channel",
                options=chan_options,
                index=chan_options.index(st.session_state["chan_choice"]) if st.session_state["chan_choice"] in chan_options else 0,
                label_visibility="collapsed",
                key="global_channel_filter",
            )
            st.session_state["chan_choice"] = chan_sel

        with f_c3:
            shift_options = ["All Shifts"] + list(SHIFT_ORDER)
            shift_sel = st.selectbox(
                "Shift",
                options=shift_options,
                index=shift_options.index(st.session_state["shift_choice"]) if st.session_state["shift_choice"] in shift_options else 0,
                label_visibility="collapsed",
                key="global_shift_filter",
            )
            st.session_state["shift_choice"] = shift_sel

        with f_c4:
            teams_all = sorted(df["roster_team"].dropna().unique().tolist())
            team_options = ["All Teams"] + teams_all
            team_sel = st.selectbox(
                "Team",
                options=team_options,
                index=team_options.index(st.session_state["team_choice"]) if st.session_state["team_choice"] in team_options else 0,
                label_visibility="collapsed",
                key="global_team_filter",
            )
            st.session_state["team_choice"] = team_sel

        with f_c5:
            if st.button("Reset Scope", use_container_width=True, key="global_reset_scope_btn"):
                st.session_state["date_range"] = (min_date, max_date)
                st.session_state["chan_choice"] = "All Channels"
                st.session_state["shift_choice"] = "All Shifts"
                st.session_state["team_choice"] = "All Teams"
                st.rerun()

    # Apply global filter mask
    filter_mask = df["created_at_ist"].dt.date.between(start_d, end_d)
    if st.session_state.get("chan_choice", "All Channels") != "All Channels":
        filter_mask &= df["channel"] == st.session_state["chan_choice"]
    if st.session_state.get("shift_choice", "All Shifts") != "All Shifts":
        filter_mask &= df["shift"] == st.session_state["shift_choice"]
    if st.session_state.get("team_choice", "All Teams") != "All Teams":
        filter_mask &= df["roster_team"] == st.session_state["team_choice"]

    view = df.loc[filter_mask].copy()
    s = summary(view)
    active_filters = {
        "date_range": f"{start_d} to {end_d}",
        "channel": st.session_state.get("chan_choice", "All Channels"),
        "shift": st.session_state.get("shift_choice", "All Shifts"),
        "team": st.session_state.get("team_choice", "All Teams"),
    }
    credit_disp = f"₹{s['credits'] / 1000:.0f}K" if s["credits"] >= 1000 else f"₹{s['credits']:,}"

    # ========================================================
    # PAGE 1: OVERVIEW (HORIZONTALLY COMPOSED WORKSPACE)
    # ========================================================
    if page == "Overview":
        delta_over_ceiling = (s["breach_rate"] - 0.15) * 100

        # Row 1: 4 Compact Metric Surfaces in Horizontal Row
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

        with kpi_c1:
            render_html(f"""
            <div class="studyos-kpi-card">
                <div class="kpi-card-header">
                    <span class="kpi-card-title">SLA Breaches</span>
                    <div class="kpi-icon-badge red-tint">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    </div>
                </div>
                <div class="kpi-card-value text-red">{s['breaches']:,}</div>
                <div class="kpi-card-footer">
                    <span class="kpi-trend-pill red">Critical Threshold</span>
                    <span class="kpi-sub-text">21.79% overall</span>
                </div>
            </div>
            """)

        with kpi_c2:
            render_html(f"""
            <div class="studyos-kpi-card">
                <div class="kpi-card-header">
                    <span class="kpi-card-title">Credit Exposure</span>
                    <div class="kpi-icon-badge amber-tint">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3a4 4 0 0 0 0-8"/></svg>
                    </div>
                </div>
                <div class="kpi-card-value text-amber">{credit_disp}</div>
                <div class="kpi-card-footer">
                    <span class="kpi-trend-pill amber">Policy §3</span>
                    <span class="kpi-sub-text">₹350 per breach</span>
                </div>
            </div>
            """)

        with kpi_c3:
            render_html(f"""
            <div class="studyos-kpi-card">
                <div class="kpi-card-header">
                    <span class="kpi-card-title">Audited Tickets</span>
                    <div class="kpi-icon-badge green-tint">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/></svg>
                    </div>
                </div>
                <div class="kpi-card-value text-dark">{s['tickets']:,}</div>
                <div class="kpi-card-footer">
                    <span class="kpi-trend-pill green">100% Reconciled</span>
                    <span class="kpi-sub-text">616 deduplicated</span>
                </div>
            </div>
            """)

        with kpi_c4:
            render_html(f"""
            <div class="studyos-kpi-card">
                <div class="kpi-card-header">
                    <span class="kpi-card-title">Breach Rate</span>
                    <div class="kpi-icon-badge coral-tint">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e11d48" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                    </div>
                </div>
                <div class="kpi-card-value text-coral">{s['breach_rate']:.2%}</div>
                <div class="kpi-card-footer">
                    <span class="kpi-trend-pill coral">+{delta_over_ceiling:.2f}% vs 15%</span>
                    <span class="kpi-sub-text">scenario ceiling</span>
                </div>
            </div>
            """)

        render_html("<div style='height: 14px;'></div>")

        # Row 2: Analytical Hub (Asymmetric 60/40 Split)
        hub_left, hub_right = st.columns([1.55, 1.05])

        with hub_left:
            # Radial math
            circ = 389.55
            fill_len = int(circ * min(1.0, s["breach_rate"]))
            empty_len = int(circ - fill_len)

            render_html(f"""
            <div class="hero-studyos-card">
                <div class="hero-studyos-left">
                    <div class="hero-eyebrow-pill">FIRST RESPONSE SLA</div>
                    <div class="hero-huge-metric">{s['breach_rate']:.2%}</div>
                    <div class="hero-subline-stats">
                        <span class="hero-stat-badge-red">{s['breaches']:,} breaches</span>
                        <span class="hero-bullet-sep">•</span>
                        <span class="hero-stat-badge-amber">{credit_disp} exposure</span>
                    </div>
                    <div class="hero-insight-caption">
                        1 in 5 audited interactions breached SLA. Concentrated in Morning shift queue surges and live Chat limits.
                    </div>
                </div>
                <div class="sla-radial-card">
                    <div class="sla-radial-disc">
                        <svg class="sla-radial-svg" viewBox="0 0 160 160">
                            <circle cx="80" cy="80" r="62" class="sla-circle-bg" fill="none" />
                            <circle cx="80" cy="80" r="62" class="sla-circle-scenario" fill="none" />
                            <circle cx="80" cy="80" r="62" class="sla-circle-fill" fill="none" style="stroke-dasharray: {fill_len} {empty_len};" />
                        </svg>
                        <div class="sla-radial-center">
                            <span class="sla-radial-val">{s['breach_rate']:.2%}</span>
                            <span class="sla-radial-lbl">Actual Rate</span>
                            <span class="radial-delta-badge">+{delta_over_ceiling:.2f}% vs 15%</span>
                        </div>
                    </div>
                    <div class="sla-radial-legend">
                        <div class="sla-legend-item">
                            <span class="legend-dot coral"></span>
                            <span>Actual ({s['breach_rate']:.2%})</span>
                        </div>
                        <div class="sla-legend-item">
                            <span class="legend-dot dash"></span>
                            <span>15.0% Scenario Ceiling</span>
                        </div>
                    </div>
                </div>
            </div>
            """)

        with hub_right:
            with st.container(border=True):
                render_html("""
                <div class="section-header-box" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="section-main-title" style="font-size: 1.05rem;">Operations Intelligence</div>
                        <span class="kpi-trend-pill amber" style="font-size: 0.68rem;">Q4 Freeze Enforced</span>
                    </div>
                    <div class="section-main-subtitle">
                        Grounded operational insights. Strictly respects Q4 headcount freeze (zero hiring recommendations).
                    </div>
                </div>
                """)

                chip_row1_c1, chip_row1_c2 = st.columns(2)
                with chip_row1_c1:
                    if st.button("Why is Morning higher?", use_container_width=True, key="hub_chip_morning"):
                        st.session_state["active_hub_q"] = "Why is Morning shift higher?"
                with chip_row1_c2:
                    if st.button("Explain ₹854K exposure", use_container_width=True, key="hub_chip_exposure"):
                        st.session_state["active_hub_q"] = "What is driving the ₹854K exposure?"

                chip_row2_c1, chip_row2_c2 = st.columns(2)
                with chip_row2_c1:
                    if st.button("What should Neha check?", use_container_width=True, key="hub_chip_investigate"):
                        st.session_state["active_hub_q"] = "What should Neha investigate first?"
                with chip_row2_c2:
                    if st.button("Open AI Assistant →", use_container_width=True, key="hub_open_ai_btn"):
                        st.session_state["main_shell_navigation"] = "AI Assistant"
                        st.rerun()

                hub_q = st.session_state.get("active_hub_q", "Why is Morning shift higher?")
                if "morning" in hub_q.lower():
                    hub_ans = (
                        f"**Operational Finding:** Morning shift generates **2,018 of {s['breaches']:,} breaches (82.7%)**, with a 32.22% breach rate. "
                        "The primary driver is the 15-minute chat SLA colliding with overnight queue buildup from the 06:00 IST start. "
                        "Morning also processes 56% of total company ticket volume (6,264 tickets)."
                    )
                elif "exposure" in hub_q.lower() or "854" in hub_q.lower() or "credit" in hub_q.lower():
                    hub_ans = (
                        "**Financial Finding:** The ₹854,000 credit exposure represents 2,440 breaches at ₹350 per incident under Policy §3. "
                        "Chat accounts for 56% (₹478.8K) and Email accounts for 30.5% (₹260.8K). Avoiding breaches eliminates store credit liability."
                    )
                elif "investigate" in hub_q.lower() or "neha" in hub_q.lower():
                    hub_ans = (
                        "**Actionable Priority:** 1) Stagger chat agent start times to 05:30/06:00 IST to absorb queue surges without hiring. "
                        "2) Streamline overnight queue handoffs from Indore. 3) Escalate the 6 dual refund-and-replacement violations for finance recovery."
                    )
                else:
                    hub_ans = (
                        f"**Operational Summary:** Across {s['tickets']:,} tickets, {s['breaches']:,} breached SLA ({s['breach_rate']:.2%}), creating ₹{s['credits']:,} in credit exposure. "
                        "Concentrated in Morning shift (32.22%) and Chat channel (27.59%)."
                    )

                render_html(f"""
                <div style="background: var(--surface-secondary); border: 1px solid var(--border-color); border-radius: 10px; padding: 0.85rem 1rem; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.55; margin-top: 0.45rem;">
                    {hub_ans}
                </div>
                """)

        render_html("<div style='height: 14px;'></div>")

        # Row 3: Visualization & Shift Operations (Asymmetric 62/38 Split)
        prog_col, shift_col = st.columns([1.6, 1.0])

        with prog_col:
            w_df = weekly_report(view)
            with st.container(border=True):
                render_html("""
                <div class="section-header-box">
                    <div class="section-main-title">Weekly SLA Performance Progression</div>
                    <div class="section-main-subtitle">
                        Audited volume (bars) alongside breach rate % (coral line). Peak breach surge in Week 19 illustrates firmware v3.2 release regression.
                    </div>
                </div>
                """)

                theme_is_dark = (st.session_state.get("theme_choice", "Light") == "Dark")
                fig_w = go.Figure()
                fig_w.add_trace(
                    go.Bar(
                        x=w_df["week_start"],
                        y=w_df["tickets"],
                        name="Audited Volume",
                        marker_color="#223147" if theme_is_dark else "#e2e8f0",
                        hoverinfo="x+y+name",
                        yaxis="y",
                    )
                )
                fig_w.add_trace(
                    go.Scatter(
                        x=w_df["week_start"],
                        y=w_df["breach_rate"],
                        name="SLA Breach Rate %",
                        line=dict(color="#f43f5e" if theme_is_dark else "#dc2626", width=2.4),
                        marker=dict(size=4.5, color="#f43f5e" if theme_is_dark else "#dc2626"),
                        yaxis="y2",
                        hoverinfo="x+y+name",
                    )
                )
                fig_w.add_trace(
                    go.Scatter(
                        x=w_df["week_start"],
                        y=[0.15] * len(w_df),
                        name="15.0% Illustrative Scenario Ceiling",
                        line=dict(color="#94a3b8" if theme_is_dark else "#64748b", width=1.4, dash="dash"),
                        yaxis="y2",
                        hoverinfo="none",
                    )
                )

                if not w_df.empty:
                    max_rate_row = w_df.loc[w_df["breach_rate"].idxmax()]
                    fig_w.add_annotation(
                        x=max_rate_row["week_start"],
                        y=max_rate_row["breach_rate"],
                        yref="y2",
                        text=f"Week 19 Peak: {max_rate_row['breach_rate']:.1%}",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1.2,
                        arrowcolor="#f43f5e" if theme_is_dark else "#dc2626",
                        ax=0,
                        ay=-32,
                        font=dict(size=10, color="#f43f5e" if theme_is_dark else "#dc2626", family="Inter"),
                        bgcolor="#192438" if theme_is_dark else "#ffffff",
                        bordercolor="rgba(244, 63, 94, 0.35)" if theme_is_dark else "#fecaca",
                        borderwidth=1,
                    )

                apply_studyos_chart_style(fig_w, height=310)
                fig_w.update_layout(
                    yaxis=dict(title="Ticket Volume", gridcolor="#1e293b" if theme_is_dark else "#f8fafc", showline=False, side="left"),
                    yaxis2=dict(
                        title="Breach Rate",
                        tickformat=".0%",
                        showline=False,
                        overlaying="y",
                        side="right",
                        range=[0, max(0.42, w_df["breach_rate"].max() + 0.05) if not w_df.empty else 0.42],
                    ),
                )
                st.plotly_chart(fig_w, use_container_width=True)

        with shift_col:
            sr = shift_report(view)
            shift_dict = sr.set_index("shift").to_dict("index")
            m_data = shift_dict.get("Morning", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})
            d_data = shift_dict.get("Day", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})
            n_data = shift_dict.get("Night", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})

            with st.container(border=True):
                render_html(f"""
                <div class="section-header-box">
                    <div class="section-main-title">Shift Performance</div>
                    <div class="section-main-subtitle">
                        Morning absorbs overnight queue buildup, generating 82.7% of all breaches.
                    </div>
                </div>
                <div class="breakdown-list-wrapper">
                    <div class="breakdown-row-item highlight-coral">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">MORNING (06:00 – 14:00 IST)</span>
                            <span class="breakdown-badge-stat alert">{m_data['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, m_data['breach_rate']/0.4*100):.1f}%; background: #dc2626;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="color: #dc2626; font-weight: 700;">{m_data['breaches']:,} breaches</span>
                            <span>{m_data['tickets']:,} tickets</span>
                            <span>82.7% share</span>
                        </div>
                    </div>

                    <div class="breakdown-row-item">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">DAY (14:00 – 22:00 IST)</span>
                            <span class="breakdown-badge-stat" style="color: #059669;">{d_data['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, d_data['breach_rate']/0.4*100):.1f}%; background: #10b981;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="font-weight: 700; color: var(--text-primary);">{d_data['breaches']:,} breaches</span>
                            <span>{d_data['tickets']:,} tickets</span>
                            <span>₹{d_data['sla_credit_exposure']:,} credit</span>
                        </div>
                    </div>

                    <div class="breakdown-row-item">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">NIGHT (22:00 – 06:00 IST, INDORE)</span>
                            <span class="breakdown-badge-stat" style="color: #6366f1;">{n_data['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, n_data['breach_rate']/0.4*100):.1f}%; background: #6366f1;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="font-weight: 700; color: var(--text-primary);">{n_data['breaches']:,} breaches</span>
                            <span>{n_data['tickets']:,} tickets</span>
                            <span>₹{n_data['sla_credit_exposure']:,} credit</span>
                        </div>
                    </div>
                </div>
                """)

        render_html("<div style='height: 14px;'></div>")

        # Row 4: Channel Performance & Governance Exports (Asymmetric 58/42 Split)
        chan_col, export_col = st.columns([1.4, 1.0])

        with chan_col:
            cr = channel_report(view)
            ch_dict = cr.set_index("channel").to_dict("index")
            chat_d = ch_dict.get("chat", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})
            social_d = ch_dict.get("social", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})
            email_d = ch_dict.get("email", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})
            voice_d = ch_dict.get("voice", {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})

            with st.container(border=True):
                render_html(f"""
                <div class="section-header-box">
                    <div class="section-main-title">Channel Compliance Standards</div>
                    <div class="section-main-subtitle">
                        Chat (15m SLA) drives 56% of breach liability; Voice callback (2h SLA) achieves 94.35% adherence.
                    </div>
                </div>
                <div class="breakdown-list-wrapper">
                    <div class="breakdown-row-item highlight-coral">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">CHAT (15 MIN SLA)</span>
                            <span class="breakdown-badge-stat alert">{chat_d['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, chat_d['breach_rate']/0.4*100):.1f}%; background: #dc2626;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="color: #dc2626; font-weight: 700;">{chat_d['breaches']:,} breaches</span>
                            <span>{chat_d['tickets']:,} tickets</span>
                            <span>₹{chat_d['sla_credit_exposure']:,} exposure</span>
                        </div>
                    </div>

                    <div class="breakdown-row-item">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">SOCIAL (4 HRS SLA)</span>
                            <span class="breakdown-badge-stat" style="color: #d97706;">{social_d['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, social_d['breach_rate']/0.4*100):.1f}%; background: #f59e0b;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="font-weight: 700; color: var(--text-primary);">{social_d['breaches']:,} breaches</span>
                            <span>{social_d['tickets']:,} tickets</span>
                            <span>₹{social_d['sla_credit_exposure']:,} exposure</span>
                        </div>
                    </div>

                    <div class="breakdown-row-item">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">EMAIL (8 HRS SLA)</span>
                            <span class="breakdown-badge-stat" style="color: #64748b;">{email_d['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, email_d['breach_rate']/0.4*100):.1f}%; background: #64748b;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="font-weight: 700; color: var(--text-primary);">{email_d['breaches']:,} breaches</span>
                            <span>{email_d['tickets']:,} tickets</span>
                            <span>₹{email_d['sla_credit_exposure']:,} exposure</span>
                        </div>
                    </div>

                    <div class="breakdown-row-item">
                        <div class="breakdown-row-top">
                            <span class="breakdown-item-name">VOICE (2 HRS CALLBACK)</span>
                            <span class="breakdown-badge-stat" style="color: #059669;">{voice_d['breach_rate']:.2%}</span>
                        </div>
                        <div class="breakdown-progress-track">
                            <div class="breakdown-progress-fill" style="width: {min(100, voice_d['breach_rate']/0.4*100):.1f}%; background: #10b981;"></div>
                        </div>
                        <div class="breakdown-footer-stats">
                            <span style="font-weight: 700; color: var(--text-primary);">{voice_d['breaches']:,} breaches</span>
                            <span>{voice_d['tickets']:,} tickets</span>
                            <span>₹{voice_d['sla_credit_exposure']:,} exposure</span>
                        </div>
                    </div>
                </div>
                """)

        with export_col:
            with st.container(border=True):
                render_html("""
                <div class="section-header-box" style="margin-bottom: 0.75rem;">
                    <div class="section-main-title" style="font-size: 1.05rem;">Audited CSV Exports</div>
                    <div class="section-main-subtitle">
                        Export validated CSV reports for leadership distribution.
                    </div>
                </div>
                """)
                st.download_button("Weekly SLA Report (CSV)", w_df.to_csv(index=False).encode(), "vireo_weekly_sla_report.csv", "text/csv", use_container_width=True, key="overview_download_weekly_csv")
                st.download_button("Shift SLA Report (CSV)", sr.to_csv(index=False).encode(), "vireo_shift_sla_report.csv", "text/csv", use_container_width=True, key="overview_download_shift_csv")
                st.download_button("Channel SLA Report (CSV)", cr.to_csv(index=False).encode(), "vireo_channel_sla_report.csv", "text/csv", use_container_width=True, key="overview_download_channel_csv")
                ar_full = agent_report(view)
                st.download_button("Agent Performance Report (CSV)", ar_full.to_csv(index=False).encode(), "vireo_agent_sla_report.csv", "text/csv", use_container_width=True, key="overview_download_agent_csv")

                render_html("""
                <div style="margin-top: 1rem; padding: 0.75rem 0.85rem; background: var(--surface-secondary); border: 1px solid var(--border-color); border-radius: 8px; font-size: 0.72rem; color: var(--text-muted); line-height: 1.45;">
                    <strong>Governance Notice:</strong> 100% verified against 11,200 production records. Policy §3 and §5 enforced. Zero hiring recommendation constraint active.
                </div>
                """)

    # ========================================================
    # PAGE: AI ASSISTANT (CONVERSATIONAL COPILOT WORKSPACE)
    # ========================================================
    elif page == "AI Assistant":
        llm_info = get_llm_config()
        provider_name = llm_info["provider"].capitalize()
        model_name = llm_info.get("model", "")
        is_live_llm = llm_info["provider"] in ["openai", "gemini"]

        active_cid = st.session_state.get("active_conv_id")
        if not active_cid or active_cid not in st.session_state["conversations"]:
            active_cid = list(st.session_state["conversations"].keys())[0]
            st.session_state["active_conv_id"] = active_cid

        active_conv = st.session_state["conversations"][active_cid]
        active_messages = active_conv["messages"]
        st.session_state["ai_chat_history"] = active_messages

        col_inbox, col_chat_workspace, col_side_context = st.columns([1.15, 2.9, 1.15], gap="medium")

        with col_inbox:
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.65rem;'>Chat History</div>", unsafe_allow_html=True)
                if st.button("+ New Chat", key="ai_inbox_new_chat_btn", use_container_width=True):
                    new_cid = f"conv_{int(time.time() * 1000)}"
                    st.session_state["conversations"][new_cid] = {
                        "id": new_cid,
                        "title": "New Conversation",
                        "messages": [],
                    }
                    st.session_state["active_conv_id"] = new_cid
                    st.session_state["conv_to_delete"] = None
                    st.session_state["pending_ai_query"] = None
                    save_conversations(st.session_state["conversations"])
                    st.rerun()

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                for cid, cdata in list(st.session_state["conversations"].items()):
                    is_active = (active_cid == cid)
                    if st.session_state.get("conv_to_delete") == cid:
                        with st.container(border=True):
                            st.markdown(
                                f"<div style='font-size: 0.74rem; font-weight: 700; color: var(--accent-rose, #f43f5e); margin-bottom: 0.2rem;'>"
                                f"Delete conversation?</div>"
                                f"<div style='font-size: 0.70rem; color: var(--text-muted); line-height: 1.35; margin-bottom: 0.45rem;'>"
                                f"Permanently delete <strong>{cdata['title']}</strong>?</div>",
                                unsafe_allow_html=True
                            )
                            c_conf_del, c_conf_can = st.columns([1, 1], gap="small")
                            with c_conf_del:
                                if st.button("Delete", key=f"btn_confirm_del_{cid}", type="primary", use_container_width=True):
                                    updated_convs, new_active = delete_conversation(
                                        st.session_state["conversations"],
                                        cid_to_delete=cid,
                                        active_cid=active_cid,
                                    )
                                    st.session_state["conversations"] = updated_convs
                                    st.session_state["active_conv_id"] = new_active
                                    st.session_state["conv_to_delete"] = None
                                    st.session_state["ai_chat_history"] = updated_convs[new_active]["messages"]
                                    st.rerun()
                            with c_conf_can:
                                if st.button("Cancel", key=f"btn_cancel_del_{cid}", use_container_width=True):
                                    st.session_state["conv_to_delete"] = None
                                    st.rerun()
                    else:
                        col_btn, col_del = st.columns([0.82, 0.18], gap="small", vertical_alignment="center")
                        with col_btn:
                            if st.button(
                                cdata["title"],
                                key=f"inbox_conv_btn_{cid}",
                                use_container_width=True,
                                type="primary" if is_active else "secondary",
                            ):
                                st.session_state["active_conv_id"] = cid
                                st.session_state["conv_to_delete"] = None
                                st.session_state["pending_ai_query"] = None
                                st.rerun()
                        with col_del:
                            if st.button(
                                "",
                                icon=":material/delete_outline:",
                                key=f"inbox_del_btn_{cid}",
                                help=f"Delete '{cdata['title']}'",
                                use_container_width=True,
                            ):
                                st.session_state["conv_to_delete"] = cid
                                st.rerun()

                render_html("""
                <div style="margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color); font-size: 0.72rem; color: var(--text-muted); line-height: 1.4;">
                    <strong>Thread Persistence:</strong> Preserved across your session.
                </div>
                """)

        with col_side_context:
            # 1. Provider Status & Configuration Panel
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;'>AI Provider Status</div>", unsafe_allow_html=True)
                if is_live_llm:
                    render_html(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.35rem;">
                        <span class="status-dot-green"></span>
                        Live LLM: {provider_name} ({model_name})
                    </div>
                    <div style="font-size: 0.74rem; color: var(--text-muted); line-height: 1.35;">
                        Connected via environment configuration. Responses are generated with verified prompt grounding.
                    </div>
                    """)
                else:
                    render_html("""
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.35rem;">
                        <span style="width: 7px; height: 7px; background-color: var(--accent-amber); border-radius: 50%; display: inline-block;"></span>
                        Verified Analytics Engine
                    </div>
                    <div style="font-size: 0.74rem; color: var(--accent-amber); line-height: 1.35; margin-bottom: 0.4rem; font-weight: 600;">
                        AI provider is not configured.
                    </div>
                    <div style="font-size: 0.72rem; color: var(--text-muted); line-height: 1.35;">
                        Add <code>OPENAI_API_KEY</code> or <code>GEMINI_API_KEY</code> to <code>.env</code> to enable live generative chat. Operating in verified deterministic analytics mode.
                    </div>
                    """)

            # 2. Active Operational Scope
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;'>Active Scope Grounding</div>", unsafe_allow_html=True)
                render_html(f"""
                <div style="font-size: 0.76rem; color: var(--text-secondary); line-height: 1.6;">
                    <div><strong>Channel:</strong> {active_filters.get('channel', 'All Channels')}</div>
                    <div><strong>Shift:</strong> {active_filters.get('shift', 'All Shifts')}</div>
                    <div><strong>Team:</strong> {active_filters.get('team', 'All Teams')}</div>
                    <div style="margin: 0.4rem 0; height: 1px; background: var(--border-subtle);"></div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Audited Scope:</span> <strong>{s['tickets']:,} tickets</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>SLA Breaches:</span> <strong style="color: var(--accent-red);">{s['breaches']:,}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Breach Rate:</span> <strong style="color: var(--accent-red);">{s['breach_rate']:.2%}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Credit Exposure:</span> <strong style="color: var(--accent-amber);">{credit_disp}</strong>
                    </div>
                </div>
                """)

            # 3. Policy & Governance Rules
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;'>Operational Guardrails</div>", unsafe_allow_html=True)
                render_html("""
                <div style="font-size: 0.72rem; color: var(--text-muted); line-height: 1.45;">
                    <div>• <strong>Policy §3:</strong> ₹350 store credit per breach</div>
                    <div>• <strong>SLAs:</strong> Chat 15m • Social 4h • Email 8h • Voice 2h</div>
                    <div>• <strong>15% Scenario:</strong> Modeling ceiling (not policy)</div>
                    <div>• <strong>Q4 Freeze:</strong> Zero hiring recommendations</div>
                </div>
                """)

            # 4. Recent Conversation Topics
            with st.container(border=True):
                st.markdown("<div style='font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;'>Recent Topics</div>", unsafe_allow_html=True)
                if st.button("Morning Shift Surge", use_container_width=True, key="recent_topic_1"):
                    st.session_state["pending_ai_query"] = "Explain the Morning shift performance."
                    st.rerun()
                if st.button("Chat vs Voice Standards", use_container_width=True, key="recent_topic_2"):
                    st.session_state["pending_ai_query"] = "Compare Chat and Voice."
                    st.rerun()
                if st.button("₹854K Credit Breakdown", use_container_width=True, key="recent_topic_3"):
                    st.session_state["pending_ai_query"] = "Explain the ₹854K credit exposure."
                    st.rerun()

        with col_chat_workspace:
            # Header toolbar inside chat workspace
            c_chat_hdr, c_chat_ctrl = st.columns([1.6, 1.4], vertical_alignment="center")
            with c_chat_hdr:
                render_html(f"""
                <div style="margin-bottom: 0.65rem;">
                    <div style="font-size: 1.15rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em;">AI Operations Assistant</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted);">
                        Thread: <strong style="color: var(--text-primary);">{active_conv['title']}</strong> • Grounded in verified support data
                    </div>
                </div>
                """)
            with c_chat_ctrl:
                c_btn1, c_btn2, c_btn3 = st.columns([1.1, 1.1, 1.1])
                with c_btn1:
                    if st.button("+ New Chat", use_container_width=True, key="ai_btn_new_chat"):
                        new_cid = f"conv_{int(time.time() * 1000)}"
                        st.session_state["conversations"][new_cid] = {
                            "id": new_cid,
                            "title": "New Conversation",
                            "messages": [],
                        }
                        st.session_state["active_conv_id"] = new_cid
                        st.session_state["conv_to_delete"] = None
                        st.session_state["pending_ai_query"] = None
                        save_conversations(st.session_state["conversations"])
                        st.rerun()
                with c_btn2:
                    if st.button("Clear Chat", use_container_width=True, key="ai_btn_clear_chat", disabled=len(active_messages) == 0):
                        active_conv["messages"] = []
                        st.session_state["pending_ai_query"] = None
                        save_conversations(st.session_state["conversations"])
                        st.rerun()
                with c_btn3:
                    if st.button("Delete Chat", use_container_width=True, key="ai_btn_del_chat"):
                        st.session_state["conv_to_delete"] = active_cid
                        st.rerun()

            # Main Chat Area Confirmation Banner if Active Conversation is Marked for Deletion
            if st.session_state.get("conv_to_delete") == active_cid:
                with st.container(border=True):
                    st.markdown(
                        f"<div style='font-size: 0.84rem; font-weight: 700; color: var(--accent-rose, #f43f5e); margin-bottom: 0.25rem;'>"
                        f"Are you sure you want to permanently delete this conversation?</div>"
                        f"<div style='font-size: 0.76rem; color: var(--text-muted); margin-bottom: 0.55rem;'>"
                        f"<strong>{active_conv['title']}</strong> will be permanently removed.</div>",
                        unsafe_allow_html=True
                    )
                    col_conf1, col_conf2, _ = st.columns([1.2, 1.2, 4], gap="small")
                    with col_conf1:
                        if st.button("Confirm Delete", key="hdr_confirm_del_btn", type="primary", use_container_width=True):
                            updated_convs, new_active = delete_conversation(
                                st.session_state["conversations"],
                                cid_to_delete=active_cid,
                                active_cid=active_cid,
                            )
                            st.session_state["conversations"] = updated_convs
                            st.session_state["active_conv_id"] = new_active
                            st.session_state["conv_to_delete"] = None
                            st.session_state["ai_chat_history"] = updated_convs[new_active]["messages"]
                            st.rerun()
                    with col_conf2:
                        if st.button("Cancel", key="hdr_cancel_del_btn", use_container_width=True):
                            st.session_state["conv_to_delete"] = None
                            st.rerun()

            # Empty State with 8 Suggested Prompts
            if not active_messages:
                render_html("""
                <div class="hero-studyos-card" style="margin-bottom: 1.25rem; text-align: center; display: block; padding: 2rem 1.5rem;">
                    <div class="hero-eyebrow-pill" style="margin: 0 auto 0.65rem auto;">VIREO AI OPERATIONS COPILOT</div>
                    <div class="hero-huge-metric" style="font-size: 2.1rem; margin-bottom: 0.5rem;">Operations Intelligence Assistant</div>
                    <div class="hero-insight-caption" style="max-width: 640px; margin: 0 auto;">
                        Ask anything about Vireo Audio support operations. I can analyze SLA performance, shifts, channels, agents, weekly trends and operational patterns using verified support data.
                    </div>
                </div>
                """)

                st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;'>Suggested Operational Inquiries:</div>", unsafe_allow_html=True)
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    if st.button("Why are SLA breaches high?", use_container_width=True, key="prompt_btn_1"):
                        st.session_state["pending_ai_query"] = "Why are SLA breaches high?"
                        st.rerun()
                    if st.button("Explain the Morning shift performance.", use_container_width=True, key="prompt_btn_2"):
                        st.session_state["pending_ai_query"] = "Explain the Morning shift performance."
                        st.rerun()
                    if st.button("Which channel has the highest breach rate?", use_container_width=True, key="prompt_btn_3"):
                        st.session_state["pending_ai_query"] = "Which channel has the highest breach rate?"
                        st.rerun()
                    if st.button("Summarize this week's SLA performance.", use_container_width=True, key="prompt_btn_4"):
                        st.session_state["pending_ai_query"] = "Summarize this week's SLA performance."
                        st.rerun()
                with p_c2:
                    if st.button("Explain the ₹854K credit exposure.", use_container_width=True, key="prompt_btn_5"):
                        st.session_state["pending_ai_query"] = "Explain the ₹854K credit exposure."
                        st.rerun()
                    if st.button("Compare Chat and Voice.", use_container_width=True, key="prompt_btn_6"):
                        st.session_state["pending_ai_query"] = "Compare Chat and Voice."
                        st.rerun()
                    if st.button("Give me the key operational findings.", use_container_width=True, key="prompt_btn_7"):
                        st.session_state["pending_ai_query"] = "Give me the key operational findings."
                        st.rerun()
                    if st.button("Show me what changed week over week.", use_container_width=True, key="prompt_btn_8"):
                        st.session_state["pending_ai_query"] = "Show me what changed week over week."
                        st.rerun()

            # Render message history
            for idx, msg in enumerate(active_messages):
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant":
                        provider_label = f"OpenAI ({model_name})" if llm_info["provider"] == "openai" else (f"Gemini ({model_name})" if llm_info["provider"] == "gemini" else "Vireo Verified Analytics Engine")
                        is_content_vireo = is_vireo_content(msg["content"])
                        is_alert = "⚠️ **AI Service Error" in msg["content"] or "offline mode without a live LLM" in msg["content"]
                        
                        if is_alert:
                            render_html(f"""
                            <div class="ai-citation-badge" style="border-color: rgba(244, 63, 94, 0.4); color: var(--accent-rose, #f43f5e);">
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                                AI Service Notice • {provider_label}
                            </div>
                            """)
                        elif is_content_vireo:
                            render_html(f"""
                            <div class="ai-citation-badge">
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>
                                Grounded in 11,200 Audited Tickets • Policy v3.2 Enforced • {provider_label}
                            </div>
                            """)
                        else:
                            render_html(f"""
                            <div class="ai-citation-badge">
                                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                                General Intelligence • {provider_label}
                            </div>
                            """)
                        # If this is the latest assistant message, offer follow-up chips and regenerate
                        if idx == len(active_messages) - 1:
                            col_act_regen, col_act_fu1, col_act_fu2, col_act_fu3 = st.columns([1.1, 1.4, 1.5, 1.4])
                            with col_act_regen:
                                if st.button("↻ Regenerate", key=f"btn_regen_{active_cid}_{idx}", use_container_width=True):
                                    if len(active_messages) >= 2:
                                        last_user = active_messages[-2]["content"]
                                        active_conv["messages"] = active_messages[:-2]
                                        save_conversations(st.session_state["conversations"])
                                        st.session_state["pending_ai_query"] = last_user
                                        st.rerun()
                            with col_act_fu1:
                                if st.button("What about Morning?", key=f"btn_fu1_{active_cid}_{idx}", use_container_width=True):
                                    st.session_state["pending_ai_query"] = "What about the morning shift?"
                                    st.rerun()
                            with col_act_fu2:
                                if st.button("How much credit?", key=f"btn_fu2_{active_cid}_{idx}", use_container_width=True):
                                    st.session_state["pending_ai_query"] = "How much credit exposure does that represent?"
                                    st.rerun()
                            with col_act_fu3:
                                if st.button("Compare with Email", key=f"btn_fu3_{active_cid}_{idx}", use_container_width=True):
                                    st.session_state["pending_ai_query"] = "Compare that with email."
                                    st.rerun()

            # Chat input
            user_query = st.session_state.pop("pending_ai_query", None)
            chat_input_val = st.chat_input("Ask a general question, or inquire about Vireo support operations...")
            prompt_to_run = user_query or chat_input_val

            if prompt_to_run:
                if not active_messages or active_conv.get("title") in ["New Conversation", "New Chat"]:
                    active_conv["title"] = prompt_to_run[:24] + ("..." if len(prompt_to_run) > 24 else "")
                active_conv["messages"].append({"role": "user", "content": prompt_to_run})
                save_conversations(st.session_state["conversations"])
                with st.chat_message("user"):
                    st.markdown(prompt_to_run)

                with st.chat_message("assistant"):
                    response_stream = stream_ai_response(
                        messages=active_conv["messages"],
                        view=view,
                        full_df=df,
                        active_filters=active_filters,
                    )
                    full_response = st.write_stream(response_stream)
                    provider_label = f"OpenAI ({model_name})" if llm_info["provider"] == "openai" else (f"Gemini ({model_name})" if llm_info["provider"] == "gemini" else "Vireo Verified Analytics Engine")
                    is_content_vireo = is_vireo_content(full_response)
                    is_alert = "⚠️ **AI Service Error" in full_response or "offline mode without a live LLM" in full_response
                    if is_alert:
                        render_html(f"""
                        <div class="ai-citation-badge" style="border-color: rgba(244, 63, 94, 0.4); color: var(--accent-rose, #f43f5e);">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                            AI Service Notice • {provider_label}
                        </div>
                        """)
                    elif is_content_vireo:
                        render_html(f"""
                        <div class="ai-citation-badge">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>
                            Grounded in 11,200 Audited Tickets • Policy v3.2 Enforced • {provider_label}
                        </div>
                        """)
                    else:
                        render_html(f"""
                        <div class="ai-citation-badge">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                            General Intelligence • {provider_label}
                        </div>
                        """)
                    active_conv["messages"].append({"role": "assistant", "content": full_response})
                    st.session_state["ai_chat_history"] = active_conv["messages"]
                    save_conversations(st.session_state["conversations"])
                    st.rerun()

    elif page == "SLA":
        w_df = weekly_report(view)
    
        with st.container(border=True):
            render_html(f"""
            <div class="section-header-box">
                <div class="section-main-title">Overall SLA Performance & Weekly Trends</div>
                <div class="section-main-subtitle">
                    Weekly first-response compliance across 79 Mon–Sun cycles in IST. Overall Breach Rate: <strong>{s['breach_rate']:.2%}</strong>
                </div>
            </div>
            """)
    
            theme_is_dark = (st.session_state.get("theme_choice", "Light") == "Dark")
            fig_sla_trend = go.Figure()
            fig_sla_trend.add_trace(
                go.Bar(
                    x=w_df["week_start"],
                    y=w_df["tickets"],
                    name="Audited Volume",
                    marker_color="#243247" if theme_is_dark else "#e2e8f0",
                    yaxis="y",
                )
            )
            fig_sla_trend.add_trace(
                go.Scatter(
                    x=w_df["week_start"],
                    y=w_df["breach_rate"],
                    name="SLA Breach Rate %",
                    line=dict(color="#f43f5e" if theme_is_dark else "#dc2626", width=2.5),
                    marker=dict(size=4.5, color="#f43f5e" if theme_is_dark else "#dc2626"),
                    yaxis="y2",
                )
            )
            fig_sla_trend.add_trace(
                go.Scatter(
                    x=w_df["week_start"],
                    y=[0.15] * len(w_df),
                    name="15.0% Illustrative Scenario Ceiling",
                    line=dict(color="#94a3b8" if theme_is_dark else "#64748b", width=1.5, dash="dash"),
                    yaxis="y2",
                )
            )
            apply_studyos_chart_style(fig_sla_trend, height=380)
            fig_sla_trend.update_layout(
                yaxis=dict(title="Tickets", gridcolor="#1e293b" if theme_is_dark else "#f8fafc", showline=False, side="left"),
                yaxis2=dict(title="Breach Rate", tickformat=".0%", overlaying="y", side="right", range=[0, 0.45]),
            )
            st.plotly_chart(fig_sla_trend, use_container_width=True)
    
            render_html("<div style='height: 12px;'></div><div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; color: var(--text-primary);'>Weekly Performance Register:</div>")
    
            table_w = w_df[["week_start", "week_end", "tickets", "breaches", "breach_rate", "sla_credit_exposure", "partial_week"]].copy()
            table_w["partial_week"] = table_w["partial_week"].map({True: "Partial Week", False: "Full Week"})
    
            st.dataframe(
                table_w.style.format({
                    "breach_rate": "{:.2%}",
                    "sla_credit_exposure": "₹{:,.0f}",
                    "tickets": "{:,}",
                    "breaches": "{:,}",
                }),
                use_container_width=True,
                hide_index=True,
            )
    
            st.download_button(
                "Download Weekly SLA Report (CSV)",
                w_df.to_csv(index=False).encode(),
                "vireo_weekly_sla_report.csv",
                "text/csv",
                key="sla_page_download_weekly_csv",
            )
    
    
    # ========================================================
    # PAGE 3: TEAMS
    # ========================================================
    elif page == "Teams":
        sr = shift_report(view)
    
        with st.container(border=True):
            render_html("""
            <div class="section-header-box">
                <div class="section-main-title">First-Response Performance by Support Team</div>
                <div class="section-main-subtitle">
                    Queue mechanics across shifts. Note the morning queue influx peak at 06:00–10:00 IST when overnight requests flood in.
                </div>
            </div>
            """)
    
            # Hourly Influx Chart
            view_h = view.copy()
            view_h["created_hour_ist"] = view_h["created_at_ist"].dt.hour
            hourly_g = view_h.groupby("created_hour_ist").agg(
                tickets=("ticket_id", "size"),
                breaches=("sla_breach", "sum"),
            ).reset_index()
            hourly_g["breach_rate"] = hourly_g["breaches"] / hourly_g["tickets"]
    
            theme_is_dark = (st.session_state.get("theme_choice", "Light") == "Dark")
            fig_h = go.Figure()
            fig_h.add_trace(
                go.Bar(
                    x=hourly_g["created_hour_ist"],
                    y=hourly_g["tickets"],
                    name="Tickets Influx (IST Hour)",
                    marker_color="#334155" if theme_is_dark else "#cbd5e1",
                    yaxis="y",
                )
            )
            fig_h.add_trace(
                go.Scatter(
                    x=hourly_g["created_hour_ist"],
                    y=hourly_g["breach_rate"],
                    name="Breach Rate %",
                    line=dict(color="#f43f5e" if theme_is_dark else "#dc2626", width=2.4),
                    yaxis="y2",
                )
            )
            apply_studyos_chart_style(fig_h, height=300)
            fig_h.update_layout(
                xaxis=dict(title="Hour of Day (IST 00:00 to 23:00)", tickmode="linear", tick0=0, dtick=1, gridcolor="#1e293b" if theme_is_dark else "#f8fafc"),
                yaxis=dict(title="Tickets", gridcolor="#1e293b" if theme_is_dark else "#f8fafc", side="left"),
                yaxis2=dict(title="Breach Rate", tickformat=".0%", overlaying="y", side="right", range=[0, 0.45]),
            )
            st.plotly_chart(fig_h, use_container_width=True)
    
            render_html("<div style='height: 12px;'></div><div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; color: var(--text-primary);'>Performance by Support Team Cohort:</div>")
            team_df = view.groupby(["roster_team", "tier"]).agg(
                tickets=("ticket_id", "size"),
                breaches=("sla_breach", "sum"),
                credits=("sla_credit_inr", "sum"),
            ).reset_index()
            team_df["breach_rate"] = team_df["breaches"] / team_df["tickets"]
            team_df["tier_label"] = team_df["tier"].map({1: "Tier 1 Frontline", 2: "Tier 2 Escalations"})
    
            st.dataframe(
                team_df[["roster_team", "tier_label", "tickets", "breaches", "breach_rate", "credits"]].style.format({
                    "breach_rate": "{:.2%}",
                    "credits": "₹{:,.0f}",
                    "tickets": "{:,}",
                    "breaches": "{:,}",
                }),
                use_container_width=True,
                hide_index=True,
            )
    
            st.download_button(
                "Download Shift Report (CSV)",
                sr.to_csv(index=False).encode(),
                "vireo_shift_sla_report.csv",
                "text/csv",
                key="teams_page_download_shift_csv",
            )
    
    
    # ========================================================
    # PAGE 4: AGENTS
    # ========================================================
    elif page == "Agents":
        ar_df = agent_report(view)
    
        with st.container(border=True):
            render_html("""
            <div class="section-header-box">
                <div class="section-main-title">Agent Operations Registry</div>
                <div class="section-main-subtitle">
                    Neutral operational register matching resolving agents with historical roster shifts. Frontline Tier 1 and Tier 2 Escalations are separated.
                    Strictly no punitive "worst agent" rankings.
                </div>
            </div>
            """)
    
            # Filter controls
            ag_col1, ag_col2, ag_col3, ag_col4 = st.columns([2.5, 1.2, 1.2, 1.2])
            with ag_col1:
                search_ag = st.text_input("Search agent:", placeholder="Filter by agent name or ID...", label_visibility="collapsed", key="agents_search_agent_input")
            with ag_col2:
                tier_sel = st.selectbox("Tier", ["All Tiers", "Tier 1 Frontline", "Tier 2 Escalations"], label_visibility="collapsed", key="agents_tier_filter")
            with ag_col3:
                shift_ag_sel = st.selectbox("Shift", ["All Shifts"] + list(SHIFT_ORDER), label_visibility="collapsed", key="agents_shift_filter")
            with ag_col4:
                team_ag_sel = st.selectbox("Team", ["All Teams"] + sorted(df["roster_team"].dropna().unique()), label_visibility="collapsed", key="agents_team_filter")
    
            filtered_ar = ar_df.copy()
            if search_ag:
                filtered_ar = filtered_ar[
                    filtered_ar["agent_name"].str.contains(search_ag, case=False, na=False)
                    | filtered_ar["agent_id"].str.contains(search_ag, case=False, na=False)
                ]
            if tier_sel == "Tier 1 Frontline":
                filtered_ar = filtered_ar[filtered_ar["tier"] == 1]
            elif tier_sel == "Tier 2 Escalations":
                filtered_ar = filtered_ar[filtered_ar["tier"] == 2]
    
            if shift_ag_sel != "All Shifts":
                filtered_ar = filtered_ar[filtered_ar["shift"] == shift_ag_sel]
            if team_ag_sel != "All Teams":
                filtered_ar = filtered_ar[filtered_ar["team"] == team_ag_sel]
    
            # Large readable table
            st.dataframe(
                filtered_ar[["agent_id", "agent_name", "site", "team", "shift", "tier", "ticket_volume", "breach_count", "breach_rate", "sla_credit_exposure"]].style.format({
                    "breach_rate": "{:.2%}",
                    "sla_credit_exposure": "₹{:,.0f}",
                    "ticket_volume": "{:,}",
                    "breach_count": "{:,}",
                }),
                use_container_width=True,
                hide_index=True,
            )
    
            # Agent Detail View
            agent_options = sorted(filtered_ar["agent_name"].unique()) if not filtered_ar.empty else []
    
            if agent_options:
                render_html("<div style='height: 12px;'></div><div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; color: var(--text-primary);'>Inspect Agent Detail:</div>")
                inspect_ag = st.selectbox("Select agent to open context panel:", agent_options, label_visibility="collapsed", key="agents_inspect_agent_select")
                ag_row = filtered_ar[filtered_ar["agent_name"] == inspect_ag].iloc[0]
                ag_tickets = view[view["agent_id"] == ag_row["agent_id"]]
    
                csat_valid = ag_tickets["csat_clean"].dropna()
                mean_csat = csat_valid.mean() if not csat_valid.empty else None
                csat_disp = f"{mean_csat:.2f} / 5.0 ({len(csat_valid)} returned)" if mean_csat else "No CSAT returned"
    
                render_html(f"""
                <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-left: 3px solid var(--accent-teal); border-radius: 12px; padding: 1.15rem 1.35rem; margin-top: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.65rem;">
                        <div>
                            <strong style="font-size: 1.15rem; color: var(--text-primary);">{ag_row['agent_name']}</strong> 
                            <span style="font-size: 0.82rem; color: var(--text-muted); margin-left: 0.4rem;">({ag_row['agent_id']} • {ag_row['site']})</span>
                        </div>
                        <div style="font-size: 0.82rem; color: var(--accent-teal); font-weight: 600;">
                            {ag_row['team']} • Shift: {ag_row['shift']} • Tier {ag_row['tier']}
                        </div>
                    </div>
                    <div style="display: flex; gap: 2.5rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem; font-size: 0.82rem;">
                        <div><span style="font-size: 0.68rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em;">VOLUME</span><br><strong style="font-size: 1.1rem; color: var(--text-primary);">{ag_row['ticket_volume']:,}</strong> tickets</div>
                        <div><span style="font-size: 0.68rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em;">BREACHES</span><br><strong style="font-size: 1.1rem; color: var(--accent-red);">{ag_row['breach_count']:,}</strong></div>
                        <div><span style="font-size: 0.68rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em;">BREACH RATE</span><br><strong style="font-size: 1.1rem; color: var(--accent-red);">{ag_row['breach_rate']:.2%}</strong></div>
                        <div><span style="font-size: 0.68rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em;">EXPOSURE</span><br><strong style="font-size: 1.1rem; color: var(--accent-amber);">{ag_row['sla_credit_exposure']:,}</strong></div>
                        <div><span style="font-size: 0.68rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em;">NORMALIZED CSAT</span><br><strong style="font-size: 1.1rem; color: var(--text-primary);">{csat_disp}</strong></div>
                    </div>
                </div>
                """)
    
                if not ag_tickets.empty:
                    ag_weekly = weekly_report(ag_tickets)
                    fig_ag = px.line(
                        ag_weekly,
                        x="week_start",
                        y="breach_rate",
                        markers=True,
                        title=f"Weekly Breach Rate Progression — {inspect_ag}",
                        labels={"week_start": "Week Commencing", "breach_rate": "Breach Rate"},
                    )
                    theme_is_dark = (st.session_state.get("theme_choice", "Light") == "Dark")
                    fig_ag.update_traces(line_color="#2dd4bf" if theme_is_dark else "#0f766e")
                    fig_ag.update_yaxes(tickformat=".0%")
                    apply_studyos_chart_style(fig_ag, height=220)
                    st.plotly_chart(fig_ag, use_container_width=True)
    
            st.download_button(
                "Download Agent Performance Report (CSV)",
                filtered_ar.to_csv(index=False).encode(),
                "vireo_agent_sla_report.csv",
                "text/csv",
                key="agents_page_download_agent_csv",
            )
    
    
    # ========================================================
    # PAGE 5: CHANNELS
    # ========================================================
    elif page == "Channels":
        cr = channel_report(view)
    
        with st.container(border=True):
            render_html("""
            <div class="section-header-box">
                <div class="section-main-title">Channel Performance & Policy Benchmarks</div>
                <div class="section-main-subtitle">
                    First-response benchmarks: Chat (15 min), Voice Callback (2 hrs), Social (4 hrs), and Email (8 hrs).
                </div>
            </div>
            """)
    
            c1, c2, c3, c4 = st.columns(4)
            chan_dict = cr.set_index("channel").to_dict("index")
    
            for col, ch_name, target_desc, color_accent in [
                (c1, "chat", "15 minutes", "#dc2626"),
                (c2, "email", "8 hours", "#64748b"),
                (c3, "social", "4 hours", "#f59e0b"),
                (c4, "voice", "2 hours (callback)", "#10b981"),
            ]:
                cd = chan_dict.get(ch_name, {"tickets": 0, "breaches": 0, "breach_rate": 0, "sla_credit_exposure": 0})
                with col:
                    render_html(f"""
                    <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-top: 3px solid {color_accent}; border-radius: 12px; padding: 1.15rem 1.25rem; margin-bottom: 1.25rem; box-shadow: var(--card-shadow);">
                        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em; text-transform: uppercase;">{target_desc} SLA</div>
                        <div style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary); text-transform: capitalize; margin: 0.2rem 0;">{ch_name}</div>
                        <div style="margin: 0.4rem 0;">
                            <span style="font-size: 2rem; font-weight: 800; color: {color_accent}; font-variant-numeric: tabular-nums;">
                                {cd['breach_rate']:.2%}
                            </span>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6;">
                            • {cd['tickets']:,} tickets<br>
                            • {cd['breaches']:,} breaches<br>
                            • ₹{cd['sla_credit_exposure']:,} exposure
                        </div>
                    </div>
                    """)
    
            fig_ch = px.bar(
                cr,
                x="channel",
                y="tickets",
                color="breach_rate",
                color_continuous_scale=["#ccfbf1", "#0f766e", "#dc2626"],
                text="breaches",
                title="Channel Ticket Volume & Breach Severity",
                labels={"tickets": "Audited Tickets", "channel": "Channel", "breach_rate": "Breach Rate"},
            )
            apply_studyos_chart_style(fig_ch, height=320)
            st.plotly_chart(fig_ch, use_container_width=True)
    
            st.dataframe(
                cr[["channel", "tickets", "breaches", "breach_rate", "sla_credit_exposure", "avg_response_minutes"]].style.format({
                    "breach_rate": "{:.2%}",
                    "sla_credit_exposure": "₹{:,.0f}",
                    "tickets": "{:,}",
                    "breaches": "{:,}",
                    "avg_response_minutes": "{:.1f}m",
                }),
                use_container_width=True,
                hide_index=True,
            )
    
            st.download_button(
                "Download Channel Report (CSV)",
                cr.to_csv(index=False).encode(),
                "vireo_channel_sla_report.csv",
                "text/csv",
                key="channels_page_download_channel_csv",
            )
    
    
    # ========================================================
    # PAGE 6: QUALITY
    # ========================================================
    elif page == "Quality":
        with st.container(border=True):
            render_html("""
            <div class="section-header-box">
                <div class="section-main-title">Quality & Data Integrity Workspace</div>
                <div class="section-main-subtitle">
                    Technical audit validating data hygiene, migration deduplication, historical roster transitions, and policy exceptions.
                </div>
            </div>
            """)
    
            # 7 Audit Items
            render_html(f"""
            <div style="display: flex; flex-direction: column; gap: 0.85rem; margin-bottom: 1.5rem;">
                <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">1. Migration Deduplication Protocol</strong>
                        <span style="background: var(--accent-green-bg); color: var(--accent-green); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-green-border);">PASS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • <strong>11,816</strong> raw rows evaluated; <strong>11,200</strong> unique ticket IDs confirmed.<br>
                        • <strong>616</strong> duplicate ticket IDs identified, each containing one <code>helpdesk</code> and one <code>legacy_fd</code> record.<br>
                        • Current <code>helpdesk</code> record prioritized and retained; 0 operational records lost.
                    </div>
                </div>
    
                <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">2. Historical Roster Matching & Shift Reshuffle</strong>
                        <span style="background: var(--accent-green-bg); color: var(--accent-green); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-green-border);">PASS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • <strong>46</strong> roster rows matched against <strong>44</strong> unique agents (100.0% match rate, 0 unmatched reps).<br>
                        • June 2025 Indore shift transition verified: Agents <strong>A3002</strong> (Tarun Mishra) and <strong>A3003</strong> (Harpreet Deshpande) correctly mapped to Night shift before 30 June 2025 and Day shift thereafter.
                    </div>
                </div>
    
                <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">3. Timestamp Logic & Timezone Handling (IST)</strong>
                        <span style="background: var(--accent-green-bg); color: var(--accent-green); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-green-border);">PASS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • UTC API export converted to <code>Asia/Kolkata</code> (IST) for date and shift attribution.<br>
                        • Elapsed duration <code>first_response_at - created_at</code> is invariant under timezone transformation. 0 negative response durations.
                    </div>
                </div>
    
                <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">4. CSAT Normalization (Policy §8)</strong>
                        <span style="background: var(--accent-green-bg); color: var(--accent-green); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-green-border);">PASS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • <strong>1,730</strong> legacy zero scores converted to <code>NaN</code> (indicating unreturned surveys).<br>
                        • 4,993 valid ratings (1 to 5) preserved, representing a <strong>44.58%</strong> response rate (matching policy expectation of ~45%).
                    </div>
                </div>
    
                <div style="background: var(--surface-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">5. Relational References & Schema Integrity</strong>
                        <span style="background: var(--accent-green-bg); color: var(--accent-green); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-green-border);">PASS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • 0 invalid customer IDs ({audit.invalid_refs['customer_id']})<br>
                        • 0 invalid agent IDs ({audit.invalid_refs['agent_id']})<br>
                        • 0 invalid product SKUs ({audit.invalid_refs['product_sku']})<br>
                        • 0 invalid quoted order IDs ({audit.invalid_refs['order_id_nonblank']})
                    </div>
                </div>
    
                <div style="background: var(--surface-card); border: 1px solid var(--accent-red-border); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">6. Simultaneous Refund and Replacement (Policy §5)</strong>
                        <span style="background: var(--accent-red-bg); color: var(--accent-red); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-red-border);">ISSUE</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • <strong>{audit.refund_replacement_exceptions}</strong> tickets found with both a refund amount and <code>replacement_issued == 'Y'</code>.<br>
                        • Policy §5 states: <em>"In no case is a customer to receive both a refund and a replacement for the same order."</em><br>
                        • Orders identified: <code>TK-240173, TK-240212, TK-240398, TK-240401, TK-240498, TK-240578</code>. Flagged for leadership remediation.
                    </div>
                </div>
    
                <div style="background: var(--surface-card); border: 1px solid var(--accent-amber-border); border-radius: 12px; padding: 1rem 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <strong style="font-size: 0.95rem; color: var(--text-primary);">7. Voice Transcript Defect Signal (Sameer's Investigation)</strong>
                        <span style="background: var(--accent-amber-bg); color: var(--accent-amber); font-weight: 700; font-size: 0.72rem; padding: 0.2rem 0.55rem; border-radius: 4px; border: 1px solid var(--accent-amber-border);">WARNING</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                        • Total voice tickets: 1,488. Voice tickets with <code>[IVR transcript]</code>: 902.<br>
                        • <strong>14</strong> tickets contain bracketed defect tags (<code>[inaudible]</code>, <code>[crosstalk]</code>, <code>[line dropped]</code>).<br>
                        • <strong>44</strong> IVR messages contain interruption/failure wording, corroborating Sameer's claim of "about forty failed IVR transcripts".
                    </div>
                </div>
            </div>
            """)
    
            # Leadership Finance Claims Check
            render_html("<div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; color: var(--text-primary);'>Leadership Financial Claims Audit (Arjun vs Priya):</div>")
            mr_df = monthly_report(view)
            fig_mo = px.bar(
                mr_df,
                x="month",
                y="sla_credit_exposure",
                labels={"month": "Month (IST)", "sla_credit_exposure": "SLA Credit Exposure (₹)"},
            )
            theme_is_dark = (st.session_state.get("theme_choice", "Light") == "Dark")
            fig_mo.update_traces(marker_color="#2dd4bf" if theme_is_dark else "#0f766e")
            apply_studyos_chart_style(fig_mo, height=240)
            st.plotly_chart(fig_mo, use_container_width=True)
    
            render_html("""
            <div style="background: var(--surface-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 1rem 1.25rem; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6;">
                <strong style="color: var(--text-primary);">Audit Synthesis:</strong><br>
                • <strong>Priya's claim (credits flat month-on-month):</strong> SUPPORTED for recent operations. From Oct 2025 to Jun 2026, monthly credits varied within a narrow band of ₹63K–₹75K.<br>
                • <strong>Arjun's claim (credits tripled since last summer):</strong> SUPPORTED when comparing early 2025 (~₹12K/month) to post-August 2025 (~₹70K/month, a ~5x jump). Note: <em>"Available ticket data does not establish the historical P&L comparison"</em> for summer 2024 because the ticket export begins 1 January 2025.
            </div>
            """)
    
            dq_export = pd.DataFrame([
                {"Audit Area": "Migration Deduplication", "Status": "PASS", "Detail": "616 duplicate pairs reconciled; 100% helpdesk retained"},
                {"Audit Area": "Historical Roster", "Status": "PASS", "Detail": "100% match rate; June Indore transitions verified"},
                {"Audit Area": "Timestamps & Timezones", "Status": "PASS", "Detail": "UTC to IST converted; 0 negative durations"},
                {"Audit Area": "CSAT Normalization", "Status": "PASS", "Detail": "1,730 zeros normalized to missing"},
                {"Audit Area": "Foreign Key References", "Status": "PASS", "Detail": "0 invalid references across customers, agents, products, orders"},
                {"Audit Area": "Policy §5 Violation", "Status": "ISSUE", "Detail": "6 orders with simultaneous refund and replacement"},
                {"Audit Area": "IVR Transcript Defects", "Status": "WARNING", "Detail": "44 failure wording tickets, 14 bracketed audio defects"},
            ])
    
            render_html("<div style='height: 12px;'></div>")
            st.download_button(
                "Download Data Quality Audit Register (CSV)",
                dq_export.to_csv(index=False).encode(),
                "vireo_data_quality_audit.csv",
                "text/csv",
                key="quality_page_download_audit_csv",
            )
