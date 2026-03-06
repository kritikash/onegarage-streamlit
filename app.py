"""J&J OneGarage — AI-Powered Innovation Hub with Streamlit UI."""

import base64
import re
import time
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as components_html

import db
from api import kickoff_chat, poll_status

# ── Page config ─────────────────────────────────────────────

st.set_page_config(
    page_title="J&J OneGarage",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load logo ───────────────────────────────────────────────

LOGO_PATH = Path("assets/onegarage_logo.svg")
LOGO_B64 = (
    base64.b64encode(LOGO_PATH.read_bytes()).decode() if LOGO_PATH.exists() else ""
)

# ── CSS ─────────────────────────────────────────────────────

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg: #FFFFFF;
    --bg-side: #FAFAFA;
    --bg-hover: #F5F5F5;
    --bg-active: rgba(235,23,0,0.05);
    --border: #E8E8E8;
    --border-lt: #F0F0F0;
    --accent: #EB1700;
    --accent-dk: #D01400;
    --accent-lt: rgba(235,23,0,0.08);
    --bubble: #2D2D2D;
    --t1: #1A1A1A;
    --t2: #555;
    --t3: #999;
    --t4: #BBB;
    --r-sm: 8px;
    --r-md: 12px;
    --r-lg: 20px;
    --r-pill: 24px;
    --f: 'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    --sh: 0 1px 3px rgba(0,0,0,0.04);
    --tr: .15s ease;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: var(--f) !important;
    background: var(--bg) !important;
}

/* Hide menu / footer / decoration — keep header for sidebar toggle */
#MainMenu, footer, div[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stMainBlockContainer"] {
    max-width: 860px;
    margin: 0 auto;
    padding: 16px 32px 0 32px !important;
}

/* ══════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: var(--bg-side) !important;
    border-right: 1px solid var(--border) !important;
    width: 272px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.sidebar-brand-text {
    font-family: var(--f); font-size: 22px; font-weight: 800;
    color: var(--accent); text-align: center; padding: 24px 16px 8px;
    letter-spacing: -0.5px;
}

/* Nav buttons */
[data-testid="stSidebar"] .stButton > button {
    width: 100%; text-align: left !important; justify-content: flex-start !important;
    background: transparent !important; border: none !important; border-radius: 0 !important;
    color: var(--t2) !important; font-family: var(--f) !important;
    font-size: 14px !important; font-weight: 500 !important;
    padding: 10px 20px !important; transition: all var(--tr) !important;
    box-shadow: none !important; line-height: 1.4 !important;
    min-height: 0 !important; margin: 0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--bg-hover) !important; color: var(--t1) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
    color: var(--accent) !important; background: var(--bg-active) !important;
    border-left: 3px solid var(--accent) !important; font-weight: 600 !important;
}

[data-testid="stSidebar"] hr {
    border-color: var(--border-lt) !important; margin: 4px 16px !important;
}

/* Expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: none !important; background: transparent !important;
    box-shadow: none !important; margin: 0 !important; padding: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details { border: none !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-family: var(--f) !important; font-size: 14px !important;
    font-weight: 500 !important; color: var(--t2) !important;
    padding: 10px 20px !important; margin: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { color: var(--t1) !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 0 8px 4px 8px !important;
}

/* Sidebar columns (for recent chat rows) */
[data-testid="stSidebar"] .stColumns { gap: 0 !important; margin: 0 !important; padding: 0 !important; }
[data-testid="stSidebar"] .stColumns [data-testid="column"] { padding: 0 !important; }

[data-testid="stSidebar"] .stColumns [data-testid="column"]:first-child .stButton > button {
    font-size: 13px !important; font-weight: 400 !important;
    padding: 7px 12px !important; border-radius: var(--r-sm) !important;
    color: var(--t2) !important; background: transparent !important;
    border: none !important; border-left: 2px solid transparent !important;
    text-align: left !important; justify-content: flex-start !important;
    line-height: 1.35 !important; white-space: nowrap !important;
    overflow: hidden !important; text-overflow: ellipsis !important;
}
[data-testid="stSidebar"] .stColumns [data-testid="column"]:first-child .stButton > button:hover {
    background: var(--bg-hover) !important; color: var(--t1) !important;
}
[data-testid="stSidebar"] .stColumns [data-testid="column"]:first-child .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stColumns [data-testid="column"]:first-child [data-testid="baseButton-primary"] {
    background: var(--accent-lt) !important; border-left: 2px solid var(--accent) !important;
    color: var(--accent) !important; font-weight: 600 !important;
}

[data-testid="stSidebar"] .stColumns [data-testid="column"]:last-child .stButton > button {
    background: transparent !important; border: none !important;
    color: var(--t4) !important; padding: 7px 4px !important;
    font-size: 12px !important; min-height: 0 !important;
    opacity: 0; transition: opacity var(--tr), color var(--tr) !important;
}
[data-testid="stSidebar"] .stColumns:hover [data-testid="column"]:last-child .stButton > button { opacity: .5; }
[data-testid="stSidebar"] .stColumns [data-testid="column"]:last-child .stButton > button:hover {
    opacity: 1; color: var(--accent) !important;
}


/* ══════════════════════════════════════════
   CHAT MESSAGES
   ══════════════════════════════════════════ */
/* Hide ALL avatar variants (Streamlit 1.30 – 1.54+) */
[data-testid="stChatMessageAvatarContainer"],
.stChatMessageAvatarContainer,
[data-testid="stChatMessage"] > div:first-child:not([data-testid="stChatMessageContent"]) {
    display: none !important;
    width: 0 !important; min-width: 0 !important;
}
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important;
    padding: 4px 0 !important; margin: 0 !important; max-width: 100% !important;
    /* Override grid so content takes full width with no avatar gap */
    grid-template-columns: 1fr !important;
    display: flex !important; flex-direction: column !important;
}
[data-testid="stChatMessageContent"] {
    width: 100% !important; max-width: 100% !important;
    display: flex !important; flex-direction: column !important;
    align-items: stretch !important;
}

/* Chat Input — match same max-width and padding as main container */
[data-testid="stChatFloatingInputContainer"] {
    max-width: 860px !important; margin: 0 auto !important;
    padding: 0 32px 14px 32px !important;
}
[data-testid="stChatInput"] {
    border-radius: var(--r-pill) !important; border-color: var(--border) !important;
}
[data-testid="stChatInput"] textarea {
    font-family: var(--f) !important; font-size: 14px !important; color: var(--t2) !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #F0A8A0, #EB7A70) !important;
    border-radius: var(--r-lg) !important; border: none !important;
}
[data-testid="stChatInput"] button svg {
    fill: var(--accent) !important; color: var(--accent) !important;
}

/* User message — dark pill, right-aligned */
.u-row { display: flex; flex-direction: column; align-items: flex-end; padding: 6px 0; }
.u-pill {
    background: var(--bubble); color: #FFF; padding: 14px 24px; border-radius: 22px 22px 4px 22px;
    font-family: var(--f); font-size: 15px; font-weight: 400; line-height: 1.55;
    max-width: 60%; text-align: left; box-shadow: var(--sh);
}
.u-ts { font-family: var(--f); font-size: 10px; color: var(--t3); margin-top: 5px; padding-right: 4px; }

/* ── Response Card (Streamlit container with border) — full width ── */
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--border) !important;
    border-radius: var(--r-md) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    width: 100% !important;
    max-width: 100% !important;
}
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 20px 24px !important;
}

/* Action button row inside response card — tighten columns */
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] .stColumns {
    gap: 2px !important;
    margin-bottom: 0 !important;
}
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] .stColumns [data-testid="column"] {
    padding: 0 !important;
}

/* Action buttons (small circles) inside response card */
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] .stColumns .stButton > button {
    width: 32px !important; height: 32px !important;
    min-height: 0 !important;
    border-radius: 50% !important;
    padding: 0 !important;
    font-size: 14px !important;
    border: 1px solid var(--border) !important;
    background: var(--bg) !important;
    color: var(--t3) !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    transition: all var(--tr) !important;
    box-shadow: none !important;
    margin: 0 auto !important;
}
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] .stColumns .stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-lt) !important;
}
/* Play button — solid red (primary type) */
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] .stColumns [data-testid="baseButton-primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #FFF !important;
}
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] .stColumns [data-testid="baseButton-primary"]:hover {
    background: var(--accent-dk) !important;
}

/* Divider inside response card */
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stDivider"] {
    margin: 0 !important; padding: 0 !important;
}
[data-testid="stChatMessage"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stDivider"] hr {
    border-color: var(--border-lt) !important;
    margin: 10px 0 14px 0 !important;
}

.resp-lbl {
    font-family: var(--f); font-size: 13px; font-weight: 700; color: var(--t1);
    letter-spacing: 0.8px; text-transform: uppercase; line-height: 32px;
}
.resp-body { font-family: var(--f); font-size: 14px; color: var(--t1); line-height: 1.75; }
.resp-body h1, .resp-body h2, .resp-body h3, .resp-body h4 {
    font-family: var(--f); color: var(--t1); margin: 18px 0 8px;
}
.resp-body h1 { font-size: 22px; font-weight: 800; }
.resp-body h2 { font-size: 19px; font-weight: 700; }
.resp-body h3 { font-size: 16px; font-weight: 700; }
.resp-body ul, .resp-body ol { padding-left: 22px; margin: 8px 0; }
.resp-body li { margin-bottom: 4px; line-height: 1.65; }
.resp-body strong { font-weight: 600; }
.resp-body p { margin: 8px 0; }
.resp-body code { background: #F3F3F3; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.resp-body blockquote {
    border-left: 3px solid var(--accent); padding-left: 14px;
    margin: 12px 0; color: var(--t2); font-style: italic;
}

/* Thinking dots */
@keyframes pdots {
    0%,20% { opacity: .15; transform: scale(.8); }
    50%    { opacity: 1;   transform: scale(1); }
    80%,100% { opacity: .15; transform: scale(.8); }
}
.td {
    display: inline-block; width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent); margin: 0 2px; animation: pdots 1.4s infinite ease-in-out;
}
.td:nth-child(1) { animation-delay: 0s; }
.td:nth-child(2) { animation-delay: .2s; }
.td:nth-child(3) { animation-delay: .4s; }
.tw { display: flex; align-items: center; gap: 10px; padding: 8px 0; }
.tl { color: var(--t3); font-family: var(--f); font-size: 13px; font-style: italic; }

/* Empty state */
.chat-empty { text-align: center; padding: 80px 0 40px; }
.chat-empty-brand {
    font-family: var(--f); font-size: 28px; font-weight: 800;
    color: var(--accent); margin-bottom: 4px;
}
.chat-empty h2 {
    font-family: var(--f); font-size: 26px; font-weight: 700; color: var(--t1); margin: 16px 0 10px;
}
.chat-empty p {
    font-family: var(--f); font-size: 15px; color: var(--t3);
    max-width: 440px; margin: 0 auto; line-height: 1.6;
}

/* Suggestion buttons */
[data-testid="stMainBlockContainer"] > div > div > .stButton > button,
.chat-suggestions .stButton > button {
    font-family: var(--f) !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    color: var(--t1) !important;
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    padding: 14px 20px !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
[data-testid="stMainBlockContainer"] > div > div > .stButton > button:hover,
.chat-suggestions .stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    box-shadow: 0 2px 8px rgba(235,23,0,0.08) !important;
}

/* ══════════════════════════════════════════
   HOMEPAGE
   ══════════════════════════════════════════ */
.hp-wrap { padding: 48px 0 40px; text-align: center; }
.hp-logo { height: 64px; width: auto; margin-bottom: 8px; }
.hp-brand {
    font-family: var(--f); font-size: 36px; font-weight: 800;
    color: var(--accent); margin-bottom: 28px; letter-spacing: -0.5px;
}
.hp-title {
    font-family: var(--f); font-size: 36px; font-weight: 800; color: var(--t1);
    line-height: 1.2; margin: 0 0 16px; letter-spacing: -0.5px;
    white-space: nowrap;
}
.hp-title span { color: var(--accent); }
.hp-sub {
    font-family: var(--f); font-size: 16px; color: var(--t2); line-height: 1.65;
    max-width: 680px; margin: 0 auto 36px; font-weight: 400; text-align: center;
}
.hp-cta {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 14px 36px; border-radius: var(--r-pill);
    background: var(--accent); color: #FFF; font-family: var(--f);
    font-size: 16px; font-weight: 600; border: none; cursor: pointer;
    text-decoration: none; transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(235,23,0,0.25);
}
.hp-cta:hover { background: var(--accent-dk); box-shadow: 0 6px 20px rgba(235,23,0,0.3); transform: translateY(-1px); }

.hp-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 56px; text-align: left; }
.hp-card {
    padding: 28px 24px; border: 1px solid var(--border); border-radius: var(--r-md);
    background: var(--bg); transition: all 0.2s ease; box-shadow: var(--sh);
}
.hp-card:hover { border-color: var(--accent); box-shadow: 0 4px 16px rgba(235,23,0,0.06); transform: translateY(-2px); }
.hp-card-icon { font-size: 28px; margin-bottom: 14px; }
.hp-card-title { font-family: var(--f); font-size: 16px; font-weight: 700; color: var(--t1); margin-bottom: 6px; }
.hp-card-desc { font-family: var(--f); font-size: 13px; color: var(--t2); line-height: 1.55; }


/* Homepage CTA button override */
[data-testid="stMainBlockContainer"] [data-testid="baseButton-primary"] {
    background: var(--accent) !important;
    color: #FFF !important;
    border: none !important;
    border-radius: var(--r-pill) !important;
    padding: 14px 32px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 14px rgba(235,23,0,0.25) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stMainBlockContainer"] [data-testid="baseButton-primary"]:hover {
    background: var(--accent-dk) !important;
    box-shadow: 0 6px 20px rgba(235,23,0,0.3) !important;
    transform: translateY(-1px) !important;
}

/* History cards */
.hc {
    background: var(--bg); border: 1px solid var(--border); border-radius: var(--r-md);
    padding: 14px 18px; margin-bottom: 10px; transition: all var(--tr); box-shadow: var(--sh);
}
.hc:hover { border-color: var(--accent); box-shadow: 0 2px 10px rgba(235,23,0,.07); }
.hc-t { font-family: var(--f); font-size: 15px; font-weight: 600; color: var(--t1); margin-bottom: 3px; }
.hc-d { font-family: var(--f); font-size: 11px; color: var(--t3); margin-bottom: 6px; }
.hc-p { font-family: var(--f); font-size: 13px; color: var(--t2); line-height: 1.4; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state ───────────────────────────────────────────

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "view" not in st.session_state:
    st.session_state.view = "home"
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "tts_text" not in st.session_state:
    st.session_state.tts_text = None
if "tts_playing_idx" not in st.session_state:
    st.session_state.tts_playing_idx = None  # msg_idx currently being spoken
if "tts_stop" not in st.session_state:
    st.session_state.tts_stop = False
if "copy_text" not in st.session_state:
    st.session_state.copy_text = None


# ── Helpers ─────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML tags from text for TTS / clipboard."""
    return re.sub(r"<[^>]+>", " ", text).strip()


def _make_title(text: str, max_len: int = 50) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "…"


def _format_time(ts: str) -> str:
    if not ts:
        return ""
    try:
        return datetime.fromisoformat(ts).strftime("%I:%M %p").lstrip("0")
    except (ValueError, TypeError):
        return ""


def _new_chat() -> None:
    st.session_state.active_chat_id = None
    st.session_state.processing = False
    st.session_state.view = "chat"


def _switch_chat(cid: str) -> None:
    st.session_state.active_chat_id = cid
    st.session_state.processing = False
    st.session_state.view = "chat"


def _delete_chat(cid: str) -> None:
    db.delete_chat(cid)
    if st.session_state.active_chat_id == cid:
        st.session_state.active_chat_id = None


def _handle_crew(cid: str, prompt: str, area) -> str | None:
    kid = kickoff_chat(prompt, cid)
    if not kid:
        return None
    for _ in range(150):
        s = poll_status(kid)
        if s["state"] == "SUCCESS" and s["result"]:
            return s["result"].get("response", "")
        if s["state"] in ("FAILURE", "TIMEOUT", "ERROR"):
            return None
        txt = s.get("last_executed_task") or "Thinking…"
        area.markdown(
            f'<div class="tw"><div><span class="td"></span><span class="td"></span>'
            f'<span class="td"></span></div><span class="tl">{txt}</span></div>',
            unsafe_allow_html=True,
        )
        time.sleep(2)
    return None


def _render_user_msg(content: str, ts: str = "") -> None:
    with st.chat_message("user"):
        ts_html = f'<div class="u-ts">{ts}</div>' if ts else ""
        st.markdown(
            f'<div class="u-row">'
            f'<div class="u-pill">{content}</div>'
            f'{ts_html}</div>',
            unsafe_allow_html=True,
        )


def _render_bot_msg(
    content: str,
    msg_idx: int,
    chat_id: str | None = None,
    user_prompt: str | None = None,
    is_last: bool = False,
) -> None:
    """Render an assistant response as a bordered card with functional action buttons."""
    with st.chat_message("assistant"):
        with st.container(border=True):
            # ── Header row: label + action buttons ──────────
            hdr = st.columns([10, 1, 1, 1, 1], gap="small")
            with hdr[0]:
                st.markdown(
                    '<span class="resp-lbl">RESPONSE</span>',
                    unsafe_allow_html=True,
                )
            with hdr[1]:
                is_speaking = st.session_state.tts_playing_idx == msg_idx
                play_icon = "⏹" if is_speaking else "▶"
                play = st.button(play_icon, key=f"play_{msg_idx}", type="primary")
            with hdr[2]:
                copy_btn = st.button("📄", key=f"copy_{msg_idx}")
            with hdr[3]:
                is_fav = db.is_favorite(chat_id) if chat_id else False
                fav_label = "❤️" if is_fav else "🤍"
                fav = st.button(fav_label, key=f"fav_{msg_idx}")
            with hdr[4]:
                retry_btn = st.button("↻", key=f"retry_{msg_idx}")

            # ── Divider ────────────────────────────────────
            st.divider()

            # ── Body ───────────────────────────────────────
            st.markdown(
                f'<div class="resp-body">{content}</div>',
                unsafe_allow_html=True,
            )

        # ── Handle actions (outside container, inside chat_message) ──
        if play:
            if is_speaking:
                # Currently speaking → stop
                st.session_state.tts_playing_idx = None
                st.session_state.tts_text = None
                st.session_state.tts_stop = True
            else:
                # Not speaking → start (cancel any other ongoing speech)
                st.session_state.tts_playing_idx = msg_idx
                st.session_state.tts_text = content
                st.session_state.tts_stop = False
        if copy_btn:
            st.session_state.copy_text = content
        if fav and chat_id:
            db.toggle_favorite(chat_id)
            st.rerun()
        if retry_btn and is_last and chat_id and user_prompt:
            db.delete_last_exchange(chat_id)
            st.session_state.pending_prompt = user_prompt
            st.rerun()


# ══════════════════════════════════════════════════════════════
#  SIDEBAR — always rendered
# ══════════════════════════════════════════════════════════════

with st.sidebar:
    # ── OneGarage Brand ──────────────────────────────────
    st.markdown(
        '<div class="sidebar-brand-text">OneGarage</div>',
        unsafe_allow_html=True,
    )

    # ── Home ─────────────────────────────────────────────
    ht = "primary" if st.session_state.view == "home" else "secondary"
    if st.button("🏠  Home", key="nav_home", type=ht,
                 use_container_width=True):
        st.session_state.view = "home"
        st.rerun()

    # ── New Chat ─────────────────────────────────────────
    if st.button("📝  New Chat", key="nav_new", use_container_width=True):
        _new_chat()
        st.rerun()

    # ── Recents ──────────────────────────────────────────
    with st.expander("🕐  Recents", expanded=True):
        all_chats = db.list_chats()
        if all_chats:
            for ch in all_chats[:8]:
                active = ch["id"] == st.session_state.active_chat_id
                title = ch["title"] or "Untitled"
                lbl = title[:25] + ("…" if len(title) > 25 else "")
                a, b = st.columns([7, 1])
                with a:
                    t = "primary" if active else "secondary"
                    if st.button(lbl, key=f"c_{ch['id']}", type=t,
                                 use_container_width=True):
                        _switch_chat(ch["id"])
                        st.rerun()
                with b:
                    if st.button("×", key=f"d_{ch['id']}"):
                        _delete_chat(ch["id"])
                        st.rerun()
        else:
            st.caption("No chats yet.")

    # ── Chats (History) ──────────────────────────────────
    ct = "primary" if st.session_state.view == "history" else "secondary"
    if st.button("💬  Chats", key="nav_chats", type=ct,
                 use_container_width=True):
        st.session_state.view = "history"
        st.rerun()

    # ── Favorites ────────────────────────────────────────
    fav_chats = db.list_favorites()
    with st.expander(f"⭐  Favorites ({len(fav_chats)})", expanded=False):
        if fav_chats:
            for fch in fav_chats[:8]:
                ftitle = (fch["title"] or "Untitled")[:25]
                if st.button(ftitle, key=f"fv_{fch['id']}",
                             use_container_width=True):
                    _switch_chat(fch["id"])
                    st.rerun()
        else:
            st.caption("Star a chat to save it here.")



# ══════════════════════════════════════════════════════════════
#  CHAT VIEW
# ══════════════════════════════════════════════════════════════

def _render_chat_view() -> None:
    aid = st.session_state.active_chat_id
    msgs = db.list_messages(aid) if aid else []
    total = len(msgs)

    for i, m in enumerate(msgs):
        ts = _format_time(m.get("created_at", ""))
        if m["role"] == "user":
            _render_user_msg(m["content"], ts)
        else:
            # Find the user prompt that preceded this assistant message
            prev_user = None
            if i > 0 and msgs[i - 1]["role"] == "user":
                prev_user = msgs[i - 1]["content"]
            is_last = i == total - 1
            _render_bot_msg(
                m["content"],
                msg_idx=i,
                chat_id=aid,
                user_prompt=prev_user,
                is_last=is_last,
            )

    # Empty state
    if not aid and not msgs:
        st.markdown(
            '<div class="chat-empty">'
            '<div class="chat-empty-brand">OneGarage</div>'
            '<h2>How can I help you today?</h2>'
            '<p>Ask about innovations, explore trends, submit ideas, '
            "or discover what's new across J&amp;J.</p>"
            '</div>',
            unsafe_allow_html=True,
        )

        # Suggestion prompts
        suggestions = [
            "Which efficiency projects saved costs?",
            "Any global efficiency initiatives?",
            "Which innovations use AI tools?",
        ]
        cols = st.columns(3, gap="medium")
        for idx, sug in enumerate(suggestions):
            with cols[idx]:
                if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                    st.session_state.pending_prompt = sug
                    st.rerun()

    # Chat input
    user_input = st.chat_input(
        "Ask about innovations, explore trends, or share an idea…",
        disabled=st.session_state.processing,
    )

    # Pending prompt (from suggestion buttons or retry) takes priority
    prompt = None
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
    elif user_input:
        prompt = user_input

    if prompt:
        if not aid:
            aid = str(uuid.uuid4())
            db.create_chat(aid, _make_title(prompt))
            st.session_state.active_chat_id = aid

        now_ts = datetime.now().strftime("%I:%M %p").lstrip("0")
        db.add_message(aid, "user", prompt)
        _render_user_msg(prompt, now_ts)

        st.session_state.processing = True
        with st.chat_message("assistant"):
            area = st.empty()
            area.markdown(
                '<div class="tw"><div><span class="td"></span><span class="td"></span>'
                '<span class="td"></span></div><span class="tl">Thinking…</span></div>',
                unsafe_allow_html=True,
            )
            result = _handle_crew(aid, prompt, area)
            area.empty()
            if result:
                db.add_message(aid, "assistant", result)
            else:
                st.error("Failed to get a response. Please try again.")

        st.session_state.processing = False
        st.rerun()


# ══════════════════════════════════════════════════════════════
#  HISTORY VIEW
# ══════════════════════════════════════════════════════════════

def _render_history_view() -> None:
    c1, c2, _ = st.columns([1, 3, 2])
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
    with c2:
        st.markdown("#### Conversation History")

    search = st.text_input(
        "Search…", placeholder="Search by title or content",
        label_visibility="collapsed",
    )
    chats = db.list_chats()
    if search:
        q = search.lower()
        chats = [
            c for c in chats
            if q in (c["title"] or "").lower()
            or q in db.get_message_preview(c["id"], max_length=200).lower()
        ]

    if not chats:
        st.info("No conversations yet. Start chatting to build your history.")
    else:
        for ch in chats:
            preview = db.get_message_preview(ch["id"])
            created = ch["created_at"][:16] if ch["created_at"] else ""
            fav_icon = " ⭐" if ch.get("favorite") else ""
            st.markdown(
                f'<div class="hc"><div class="hc-t">{ch["title"] or "Untitled"}{fav_icon}</div>'
                f'<div class="hc-d">{created}</div>'
                f'<div class="hc-p">{preview}</div></div>',
                unsafe_allow_html=True,
            )
            a, b, _ = st.columns([1, 1, 4])
            with a:
                if st.button("Open", key=f"ho_{ch['id']}"):
                    _switch_chat(ch["id"])
                    st.rerun()
            with b:
                if st.button("Delete", key=f"hd_{ch['id']}"):
                    _delete_chat(ch["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════
#  TTS & CLIPBOARD INJECTION
# ══════════════════════════════════════════════════════════════

def _inject_tts_and_clipboard() -> None:
    """Inject JavaScript for text-to-speech and clipboard copy."""

    # ── Stop speech ──────────────────────────────────────
    if st.session_state.tts_stop:
        components_html(
            """
            <script>
            (function() {
                try {
                    var s = window.parent.speechSynthesis;
                    if (s) s.cancel();
                } catch(e) {
                    var s2 = window.speechSynthesis;
                    if (s2) s2.cancel();
                }
            })();
            </script>
            """,
            height=0,
        )
        st.session_state.tts_stop = False

    # ── Start speech ─────────────────────────────────────
    if st.session_state.tts_text:
        clean = _strip_html(st.session_state.tts_text)
        # Escape for JS string
        clean = (
            clean.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", "")
        )
        # Truncate for browser TTS limits
        if len(clean) > 4000:
            clean = clean[:4000]
        components_html(
            f"""
            <script>
            (function() {{
                try {{
                    var synth = window.parent.speechSynthesis;
                }} catch(e) {{
                    var synth = window.speechSynthesis;
                }}
                if (!synth) return;
                synth.cancel();
                var u = new SpeechSynthesisUtterance('{clean}');
                u.rate = 1.0;
                u.pitch = 1.0;
                synth.speak(u);
            }})();
            </script>
            """,
            height=0,
        )
        st.session_state.tts_text = None

    if st.session_state.copy_text:
        clean = _strip_html(st.session_state.copy_text)
        clean = (
            clean.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("$", "\\$")
        )
        components_html(
            f"""
            <script>
            (function() {{
                const text = `{clean}`;
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).catch(() => {{}});
                }} else {{
                    const ta = document.createElement('textarea');
                    ta.value = text;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                }}
            }})();
            </script>
            """,
            height=0,
        )
        st.session_state.copy_text = None


# ══════════════════════════════════════════════════════════════
#  HOME VIEW
# ══════════════════════════════════════════════════════════════

def _render_home_view() -> None:
    logo_tag = (
        f'<img class="hp-logo" src="data:image/svg+xml;base64,{LOGO_B64}">'
        if LOGO_B64 else ""
    )
    st.markdown(
'<div class="hp-wrap">'
f'{logo_tag}'
'<div class="hp-brand">OneGarage</div>'
'<h1 class="hp-title">Discover. Innovate. <span>Transform.</span></h1>'
'<p class="hp-sub">'
'Your AI-powered gateway to explore innovations across '
'Johnson &amp; Johnson — surface insights, track trends, and turn ideas '
'into impact at enterprise scale.'
'</p>'
'</div>',
        unsafe_allow_html=True,
    )

    # CTA button
    _, center, _ = st.columns([2, 3, 2])
    with center:
        if st.button("🚀  Let's Get Started", key="hp_cta",
                     use_container_width=True, type="primary"):
            _new_chat()
            st.rerun()

    # Feature cards
    st.markdown(
'<div class="hp-cards">'
'<div class="hp-card">'
'<div class="hp-card-icon">🔍</div>'
'<div class="hp-card-title">Innovation Discovery</div>'
'<div class="hp-card-desc">Search and explore thousands of innovation ideas '
'across regions, categories, and business units with AI-powered insights.</div>'
'</div>'
'<div class="hp-card">'
'<div class="hp-card-icon">📊</div>'
'<div class="hp-card-title">Trend Analysis</div>'
'<div class="hp-card-desc">Identify emerging patterns, technologies, and '
'efficiency opportunities with intelligent synthesis of org-wide data.</div>'
'</div>'
'<div class="hp-card">'
'<div class="hp-card-icon">💡</div>'
'<div class="hp-card-title">Idea Generation</div>'
'<div class="hp-card-desc">Brainstorm new solutions, get AI-driven suggestions, '
'and connect dots between existing innovations across J&amp;J.</div>'
'</div>'
'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
#  ROUTING
# ══════════════════════════════════════════════════════════════

if st.session_state.view == "home":
    _render_home_view()
elif st.session_state.view == "history":
    _render_history_view()
else:
    _render_chat_view()

# Always inject TTS / clipboard at the end
_inject_tts_and_clipboard()
