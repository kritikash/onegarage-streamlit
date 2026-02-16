"""CrewAI Chat Frontend — Streamlit UI with SQLite persistence."""

import base64
import time
import uuid
from pathlib import Path

import streamlit as st

import db
from api import kickoff_chat, poll_status

# ── Page config ─────────────────────────────────────────────

st.set_page_config(
    page_title="CrewAI Chat",
    page_icon="assets/crewai_logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load logo as base64 for inline embedding ────────────────

LOGO_PATH = Path("assets/crewai_logo.svg")
LOGO_B64 = base64.b64encode(LOGO_PATH.read_bytes()).decode() if LOGO_PATH.exists() else ""

# ── CSS Design System ───────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Custom Properties ────────────────────── */
:root {
    --bg-primary: #0E1117;
    --bg-secondary: #141820;
    --bg-card: #1A1D24;
    --border-subtle: #2A2D35;
    --border-hover: #FF5A50;
    --accent: #FF5A50;
    --accent-dim: rgba(255, 90, 80, 0.08);
    --accent-glow: rgba(255, 90, 80, 0.15);
    --text-primary: #FAFAFA;
    --text-secondary: #8B8D97;
    --text-muted: #6B6E76;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Global ────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: var(--font-family) !important;
}
[data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary);
}

/* ── Hide Streamlit Branding ──────────────── */
#MainMenu, header[data-testid="stHeader"], footer,
div[data-testid="stDecoration"] {
    display: none !important;
}

/* ── Sidebar ───────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-subtle);
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
}

/* ── Chat Bubbles ─────────────────────────── */
[data-testid="stChatMessage"] {
    border-radius: var(--radius-md);
    margin-bottom: 8px;
    padding: 12px 16px;
}
/* User messages: coral tint */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: var(--accent-dim);
    border: 1px solid rgba(255, 90, 80, 0.12);
}
/* Assistant messages: card style */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
}

/* ── History Cards ─────────────────────────── */
.history-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.history-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 0 20px var(--accent-glow);
}
.history-card-title {
    font-family: var(--font-family);
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
}
.history-card-date {
    font-family: var(--font-family);
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 8px;
}
.history-card-preview {
    font-family: var(--font-family);
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.4;
}

/* ── Thinking Indicator ──────────────────── */
@keyframes thinking-dots {
    0%, 20% { opacity: 0.2; }
    50% { opacity: 1; }
    80%, 100% { opacity: 0.2; }
}
.thinking-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--accent);
    margin: 0 3px;
    animation: thinking-dots 1.4s infinite ease-in-out;
}
.thinking-dot:nth-child(1) { animation-delay: 0s; }
.thinking-dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dot:nth-child(3) { animation-delay: 0.4s; }
.thinking-container {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
}
.thinking-text {
    color: var(--text-secondary);
    font-family: var(--font-family);
    font-size: 14px;
}

/* ── Empty State ──────────────────────────── */
.empty-state {
    text-align: center;
    padding: 100px 20px 40px 20px;
    color: var(--text-muted);
}
.empty-state img {
    height: 48px;
    margin-bottom: 24px;
}
.empty-state h2 {
    font-family: var(--font-family);
    color: var(--text-primary);
    font-weight: 600;
    font-size: 24px;
    margin-bottom: 8px;
}
.empty-state p {
    font-family: var(--font-family);
    color: var(--text-secondary);
    font-size: 15px;
    margin-bottom: 32px;
}

/* ── Suggestion Chips ─────────────────────── */
.chip-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    max-width: 640px;
    margin: 0 auto;
}

/* ── Logo ──────────────────────────────────── */
.logo-sidebar {
    text-align: center;
    padding: 12px 0 4px 0;
}
.logo-sidebar img {
    height: 28px;
}

/* ── History View Header ──────────────────── */
.history-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
}
.history-header h2 {
    font-family: var(--font-family);
    color: var(--text-primary);
    font-weight: 600;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "view" not in st.session_state:
    st.session_state.view = "chat"
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ── Helpers ─────────────────────────────────────────────────

def _make_title(text: str, max_len: int = 50) -> str:
    """First 50 chars of text, truncated at word boundary."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def _new_chat() -> None:
    """Create a new chat and set it as active."""
    st.session_state.active_chat_id = None
    st.session_state.processing = False
    st.session_state.view = "chat"


def _switch_chat(chat_id: str) -> None:
    """Switch the active chat and navigate to chat view."""
    st.session_state.active_chat_id = chat_id
    st.session_state.processing = False
    st.session_state.view = "chat"


def _delete_chat(chat_id: str) -> None:
    """Delete a chat and clear active if it was the one deleted."""
    db.delete_chat(chat_id)
    if st.session_state.active_chat_id == chat_id:
        st.session_state.active_chat_id = None


def _handle_crew_response(chat_id: str, prompt: str, status_area) -> str | None:
    """Kickoff a CrewAI run and poll every 2s until done (5 min timeout)."""
    kickoff_id = kickoff_chat(prompt, chat_id)
    if not kickoff_id:
        return None

    max_attempts = 150  # 150 x 2s = 5 minutes
    for _ in range(max_attempts):
        status = poll_status(kickoff_id)

        if status["state"] == "SUCCESS" and status["result"]:
            return status["result"].get("response", "")

        if status["state"] in ("FAILURE", "TIMEOUT", "ERROR"):
            return None

        # Show current task progress if available
        task_text = status.get("last_executed_task") or "Thinking..."
        status_area.markdown(
            f'<div class="thinking-container">'
            f'<div><span class="thinking-dot"></span>'
            f'<span class="thinking-dot"></span>'
            f'<span class="thinking-dot"></span></div>'
            f'<span class="thinking-text">{task_text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        time.sleep(2)

    return None  # Timed out


# ── Render: Empty State ─────────────────────────────────────

SUGGESTIONS = [
    "Analyze our latest quarterly report",
    "Help me write a marketing strategy",
    "Research competitor pricing models",
    "Summarize key industry trends",
]


def _render_empty_state() -> None:
    """Centered empty state with logo, headline, and suggestion chips."""
    logo_html = f'<img src="data:image/svg+xml;base64,{LOGO_B64}">' if LOGO_B64 else ""
    st.markdown(
        f"""
        <div class="empty-state">
            {logo_html}
            <h2>What can your crew help with?</h2>
            <p>Start a conversation or pick a suggestion below.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suggestion chips as Streamlit buttons in a centered row
    cols = st.columns([1, 1, 1, 1])
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 4]:
            if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                st.session_state.pending_prompt = suggestion
                st.rerun()


# ── Render: Chat View ───────────────────────────────────────

def _render_chat_view() -> None:
    """Main chat interface — hero view."""
    active_id = st.session_state.active_chat_id

    if active_id:
        messages = db.list_messages(active_id)
    else:
        messages = []

    # Display existing messages
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Empty state when no chat is active and no messages
    if not active_id and not messages:
        _render_empty_state()

    # Check for pending prompt from suggestion chips
    prompt = None
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
    else:
        # Chat input — disabled while processing
        prompt = st.chat_input(
            "Message your CrewAI crew...",
            disabled=st.session_state.processing,
        )

    if prompt:
        # Lazy chat creation: generate UUID on first message
        if not active_id:
            active_id = str(uuid.uuid4())
            title = _make_title(prompt)
            db.create_chat(active_id, title)
            st.session_state.active_chat_id = active_id

        # Save & display user message
        db.add_message(active_id, "user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        # ── Kickoff + Poll ──────────────────────────────────
        st.session_state.processing = True

        with st.chat_message("assistant"):
            status_area = st.empty()

            # Show thinking indicator
            status_area.markdown(
                '<div class="thinking-container">'
                '<div><span class="thinking-dot"></span>'
                '<span class="thinking-dot"></span>'
                '<span class="thinking-dot"></span></div>'
                '<span class="thinking-text">Thinking...</span>'
                '</div>',
                unsafe_allow_html=True,
            )

            response_text = _handle_crew_response(active_id, prompt, status_area)

            # Clear thinking indicator and show response
            status_area.empty()
            if response_text:
                st.markdown(response_text)
                db.add_message(active_id, "assistant", response_text)
            else:
                st.error("Failed to get a response. Please try again.")

        st.session_state.processing = False
        st.rerun()


# ── Render: History View ────────────────────────────────────

def _render_history_view() -> None:
    """Full-screen conversation history."""
    # Back navigation
    col_back, col_title, _ = st.columns([1, 3, 2])
    with col_back:
        if st.button("< Back to Chat", use_container_width=True):
            st.session_state.view = "chat"
            st.rerun()
    with col_title:
        st.markdown("#### Conversation History")

    st.markdown("")  # spacing

    # Search
    search_query = st.text_input(
        "Search conversations...",
        placeholder="Search by title or message content",
        label_visibility="collapsed",
    )

    all_chats = db.list_chats()

    if search_query:
        query_lower = search_query.lower()
        all_chats = [
            c for c in all_chats
            if query_lower in c["title"].lower()
            or query_lower in db.get_message_preview(c["id"], max_length=200).lower()
        ]

    if not all_chats:
        st.markdown(
            '<div class="empty-state"><h2>No conversations yet</h2>'
            "<p>Start chatting to see your history here.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        for chat in all_chats:
            preview = db.get_message_preview(chat["id"])
            created = chat["created_at"][:16] if chat["created_at"] else ""

            st.markdown(
                f"""
                <div class="history-card">
                    <div class="history-card-title">{chat["title"]}</div>
                    <div class="history-card-date">{created}</div>
                    <div class="history-card-preview">{preview}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_open, col_delete, _ = st.columns([1, 1, 4])
            with col_open:
                if st.button("Open", key=f"hopen_{chat['id']}"):
                    _switch_chat(chat["id"])
                    st.rerun()
            with col_delete:
                if st.button("Delete", key=f"hdel_{chat['id']}"):
                    _delete_chat(chat["id"])
                    st.rerun()


# ── Sidebar ─────────────────────────────────────────────────

with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f'<div class="logo-sidebar"><img src="data:image/svg+xml;base64,{LOGO_B64}"></div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")

    if st.button("+ New Chat", type="primary", use_container_width=True):
        _new_chat()
        st.rerun()

    # Sidebar search
    sidebar_search = st.text_input(
        "Search chats...",
        placeholder="Filter by title or content",
        label_visibility="collapsed",
        key="sidebar_search",
    )

    st.caption("RECENT CHATS")

    chats = db.list_chats()

    # Filter by sidebar search
    if sidebar_search:
        search_lower = sidebar_search.lower()
        chats = [
            c for c in chats
            if search_lower in c["title"].lower()
            or search_lower in db.get_message_preview(c["id"], max_length=200).lower()
        ]

    for chat in chats[:15]:  # Show last 15 in sidebar
        col_btn, col_del = st.columns([5, 1])
        with col_btn:
            is_active = chat["id"] == st.session_state.active_chat_id
            label = f"{'> ' if is_active else ''}{chat['title']}"
            if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):
                _switch_chat(chat["id"])
                st.rerun()
        with col_del:
            if st.button("x", key=f"del_{chat['id']}"):
                _delete_chat(chat["id"])
                st.rerun()

    st.markdown("---")

    if st.button("View All History", use_container_width=True):
        st.session_state.view = "history"
        st.rerun()


# ── Main Content Routing ────────────────────────────────────

if st.session_state.view == "history":
    _render_history_view()
else:
    _render_chat_view()
