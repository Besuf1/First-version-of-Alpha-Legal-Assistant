from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from core.assistant import GroundedLegalAssistant
from core.knowledge import KnowledgeBase

APP_DIR = Path(__file__).parent
KNOWLEDGE_DIR = APP_DIR / "knowledge_base"
CONTACT_URL = "https://alphaadvocatesllp.com/contact/"
CONTACT_EMAIL = "info@alphaadvocates.et"
CONTACT_PHONE = "+251 91 167 9863"

st.set_page_config(
    page_title="Alpha Advocates | Legal Information Assistant",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded",
)


def get_setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then environment variables."""
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


@st.cache_resource(show_spinner=False)
def load_knowledge_base(directory: str) -> KnowledgeBase:
    return KnowledgeBase.from_directory(Path(directory))


def render_source_list(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"Sources used ({len(sources)})", expanded=False):
        for source in sources:
            label = source.get("title") or source.get("file") or "Knowledge-base source"
            heading = source.get("heading", "")
            url = source.get("url", "")
            detail = f" — {heading}" if heading and heading != label else ""
            if url:
                st.markdown(f"- [{label}]({url}){detail}")
            else:
                st.markdown(f"- **{label}**{detail}")


def render_message(message: dict) -> None:
    avatar = "⚖️" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_source_list(message.get("sources", []))


st.markdown(
    """
    <style>
    :root {
        --alpha-navy: #14243b;
        --alpha-navy-2: #203853;
        --alpha-gold: #c5a15d;
        --alpha-cream: #f7f3ea;
        --alpha-ink: #172233;
        --alpha-muted: #627083;
        --alpha-line: #e6ded0;
    }
    .stApp { background: #fbfaf7; color: var(--alpha-ink); }
    [data-testid="stHeader"] { background: rgba(251,250,247,.86); }
    [data-testid="stSidebar"] { background: var(--alpha-navy); }
    [data-testid="stSidebar"] * { color: #f7f3ea; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.16); }
    [data-testid="stSidebar"] .stButton button {
        background: var(--alpha-gold); color: #132139; border: 0; font-weight: 750;
    }
    [data-testid="stChatMessage"] {
        background: #ffffff; border: 1px solid #ece6dc; border-radius: 18px;
        box-shadow: 0 7px 24px rgba(20,36,59,.055); padding: .35rem .55rem;
    }
    [data-testid="stChatMessage"] a { color: #8a642b; }
    .alpha-brand {
        display: flex; align-items: center; gap: 18px; padding: 10px 0 18px;
        border-bottom: 1px solid var(--alpha-line); margin-bottom: 22px;
    }
    .alpha-mark {
        width: 58px; height: 58px; border-radius: 17px; display: grid; place-items: center;
        color: var(--alpha-navy); background: var(--alpha-gold); font: 800 29px Georgia, serif;
        box-shadow: 0 9px 25px rgba(99,73,31,.16);
    }
    .alpha-kicker { color: #8a642b; font-size: .77rem; letter-spacing: .16em; font-weight: 800; }
    .alpha-title { color: var(--alpha-navy); font: 700 clamp(1.55rem,4vw,2.18rem) Georgia,serif; margin: 2px 0; }
    .alpha-subtitle { color: var(--alpha-muted); font-size: .94rem; }
    .notice {
        background: var(--alpha-cream); border: 1px solid #eadfc9; border-left: 4px solid var(--alpha-gold);
        border-radius: 12px; padding: 13px 15px; margin: 4px 0 20px; color: #3d4857;
    }
    .eyebrow { color: #8a642b; font-size: .78rem; font-weight: 800; letter-spacing: .12em; }
    .welcome h2 { color: var(--alpha-navy); font: 700 1.45rem Georgia,serif; margin-bottom: .35rem; }
    .welcome p { color: var(--alpha-muted); margin-top: 0; }
    .status-pill {
        display: inline-flex; align-items: center; gap: 7px; padding: 6px 10px; border-radius: 999px;
        background: #eef7ef; color: #27613b; font-size: .78rem; font-weight: 750; margin-bottom: 10px;
    }
    .status-pill.demo { background: #fff3dc; color: #7a5520; }
    .sidebar-brand { font: 700 1.25rem Georgia,serif; color: white; margin: .2rem 0; }
    .sidebar-small { font-size: .84rem; color: #d8dfE7 !important; line-height: 1.5; }
    .mini-footer { color: #798495; font-size: .78rem; text-align: center; padding: 25px 0 6px; }
    .stButton button { border-radius: 12px; border-color: #ded6c8; min-height: 45px; }
    .stButton button:hover { border-color: var(--alpha-gold); color: var(--alpha-navy); }
    </style>
    """,
    unsafe_allow_html=True,
)

knowledge_base = load_knowledge_base(str(KNOWLEDGE_DIR))
api_key = get_setting("GEMINI_API_KEY") or get_setting("GOOGLE_API_KEY")
model_name = get_setting("GEMINI_MODEL", "gemini-3.1-flash-lite")
assistant = GroundedLegalAssistant(
    knowledge_base=knowledge_base,
    api_key=api_key,
    model_name=model_name,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="sidebar-brand">ALPHA ADVOCATES LLP</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-small">Smart legal solutions, grounded in local insight.</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**Before you continue**")
    acknowledged = st.checkbox(
        "I understand this tool provides general information, not legal advice.",
        value=st.session_state.get("acknowledged", False),
        key="acknowledged",
    )
    st.caption("Please do not enter confidential, privileged, or highly sensitive information.")
    st.divider()
    st.markdown("**Speak with the firm**")
    st.markdown(f"📞 {CONTACT_PHONE}")
    st.markdown(f"✉️ [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})")
    st.link_button("Book a consultation", CONTACT_URL, use_container_width=True)
    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    with st.expander("System status"):
        st.write(f"Knowledge sources: {knowledge_base.source_count}")
        st.write(f"Knowledge chunks: {knowledge_base.chunk_count}")
        st.write("AI: Connected" if assistant.ai_enabled else "AI: Demo mode")
        if assistant.ai_enabled:
            st.caption(f"Model: {model_name}")

st.markdown(
    """
    <div class="alpha-brand">
      <div class="alpha-mark">α</div>
      <div>
        <div class="alpha-kicker">ALPHA ADVOCATES LLP</div>
        <div class="alpha-title">Legal Information Assistant</div>
        <div class="alpha-subtitle">Clear, grounded information for doing business in Ethiopia.</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if assistant.ai_enabled:
    st.markdown('<div class="status-pill">● Knowledge base connected</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="status-pill demo">● Demo mode — add a Gemini API key for generated answers</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="notice">
      <strong>General information only.</strong> This assistant uses a curated Alpha Advocates
      knowledge base. It cannot assess your facts, create a lawyer-client relationship, or replace a lawyer.
    </div>
    """,
    unsafe_allow_html=True,
)

for saved_message in st.session_state.messages:
    render_message(saved_message)

selected_prompt = None
if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome">
          <div class="eyebrow">START HERE</div>
          <h2>How may we help?</h2>
          <p>Ask about the firm, its practice areas, or lawyer-reviewed materials in the knowledge base.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    suggestions = [
        "What services do you provide for startups?",
        "Can Alpha Advocates help a foreign investor?",
        "How can I book a consultation?",
        "What corporate and commercial services do you offer?",
    ]
    left, right = st.columns(2)
    for index, suggestion in enumerate(suggestions):
        container = left if index % 2 == 0 else right
        with container:
            if st.button(suggestion, key=f"suggestion_{index}", use_container_width=True, disabled=not acknowledged):
                selected_prompt = suggestion

user_prompt = st.chat_input(
    "Ask a general legal-information question…",
    disabled=not acknowledged,
)
prompt = user_prompt or selected_prompt

if prompt:
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    render_message(user_message)

    prior_history = st.session_state.messages[:-1]
    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Reviewing the approved knowledge base…"):
            result = assistant.answer(prompt, prior_history)
        st.markdown(result.text)
        render_source_list(result.sources)

    st.session_state.messages.append(
        {"role": "assistant", "content": result.text, "sources": result.sources}
    )

st.markdown(
    '<div class="mini-footer">Alpha Advocates LLP · Addis Ababa, Ethiopia · Your privacy matters</div>',
    unsafe_allow_html=True,
)
