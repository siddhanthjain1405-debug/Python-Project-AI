"""Streamlit web interface for the Memory Agent.

Run locally:  streamlit run app.py
"""

import streamlit as st

from memory_agent import (
    AIError,
    OpenRouterClient,
    MemoryStoreError,
    chat_with_memory,
    load_settings,
    open_store,
)
from memory_agent.config import MAX_MESSAGE_CHARS

st.set_page_config(page_title="Memory Agent", page_icon="🧠", layout="wide")

settings = load_settings()

st.markdown(
    """
    <style>
    .block-container {max-width: 1100px; padding-top: 2rem;}
    [data-testid="stChatMessage"] {border-radius: 14px; padding: 0.6rem 0.9rem;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,0.2);}
    .app-title {font-size: 1.6rem; font-weight: 700; margin-bottom: 0;}
    .app-sub {opacity: 0.7; margin-top: 0; margin-bottom: 0.8rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_store(profile: str, path: str):
    return open_store(profile, path)


@st.cache_resource(show_spinner=False)
def get_llm(api_key: str, model: str):
    return OpenRouterClient(api_key, model)


# ---------------------------------------------------------------- session state
st.session_state.setdefault("messages", [])
st.session_state.setdefault("confirm_clear", False)

# --------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🧠 Memory Agent")
    st.caption("An AI assistant that remembers you across sessions.")

    profile = st.text_input(
        "Memory profile",
        value="default",
        help="Each profile has its own separate memory. Use a unique name so other "
        "visitors on a shared deployment don't see your memories.",
    ).strip() or "default"

    user_key = st.text_input(
        "OpenRouter API key (optional)",
        type="password",
        help="Used only for this session and never stored. Leave empty to use the "
        "server's OPENROUTER_API_KEY, if one is configured.",
    ).strip()
    model = settings.model
    st.caption(f"Model: `{model}` (free models only)")
    top_k = st.slider("Memories recalled per message", 1, 10, settings.top_k)

    api_key = user_key or settings.api_key
    if api_key:
        st.success("AI mode: OpenRouter connected")
    else:
        st.warning("Demo mode: no API key. Memory works, but no AI replies are generated.")

    if st.button("Clear chat window", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

try:
    store = get_store(profile, settings.memory_dir)
except MemoryStoreError as exc:
    st.error(str(exc))
    st.stop()

llm = None
if api_key:
    try:
        llm = get_llm(api_key, model)
    except AIError as exc:
        st.sidebar.error(str(exc))

with st.sidebar:
    st.metric("Stored memories", store.count())

# ------------------------------------------------------------------------ tabs
st.markdown('<p class="app-title">🧠 Personal AI Agent</p>'
            '<p class="app-sub">Chat with an assistant that remembers you across sessions.</p>',
            unsafe_allow_html=True)
chat_tab, memory_tab = st.tabs(["💬 Chat", "🗄️ Memory vault"])

with chat_tab:
    if not st.session_state.messages:
        st.info("Tell me something about yourself, then ask about it later (even in a new "
                "session) to see the memory in action.")

    for entry in st.session_state.messages:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])
            if entry.get("memories"):
                with st.expander("Memories recalled"):
                    for memory in entry["memories"]:
                        st.write(f"• {memory}")

    prompt = st.chat_input("Type a message...", max_chars=MAX_MESSAGE_CHARS)
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        try:
            with st.spinner("Thinking..."):
                result = chat_with_memory(
                    store, llm, prompt, st.session_state.messages, top_k
                )
        except ValueError as exc:
            st.warning(str(exc))
        except (AIError, MemoryStoreError) as exc:
            st.error(str(exc))
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            if result.demo_mode:
                note = ("Demo mode: no AI reply was generated because no API key is "
                        "configured. Your message was saved to memory.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"*{note}*", "memories": result.memories_used}
                )
            else:
                st.session_state.messages.append(
                    {"role": "assistant", "content": result.reply, "memories": result.memories_used}
                )
            st.rerun()

with memory_tab:
    st.subheader("Add a fact manually")
    with st.form("add_memory", clear_on_submit=True):
        new_fact = st.text_area("Fact to remember", max_chars=MAX_MESSAGE_CHARS, height=80)
        if st.form_submit_button("Save memory"):
            try:
                store.add(new_fact, source="manual")
                st.rerun()
            except MemoryStoreError as exc:
                st.error(str(exc))

    st.subheader("Stored memories")
    query = st.text_input("Filter by text", placeholder="Type to filter...").strip().lower()
    try:
        items = [i for i in store.list_items() if query in i.text.lower()]
    except MemoryStoreError as exc:
        st.error(str(exc))
        items = []

    if not items:
        st.write("No memories to show.")
    for item in items:
        col_text, col_btn = st.columns([8, 1])
        with col_text:
            st.write(item.text)
            if item.created_at:
                st.caption(item.created_at[:19].replace("T", " ") + " UTC")
        with col_btn:
            if st.button("🗑️", key=f"del_{item.id}", help="Delete this memory"):
                try:
                    store.delete(item.id)
                    st.rerun()
                except MemoryStoreError as exc:
                    st.error(str(exc))

    st.divider()
    left, right = st.columns(2)
    with left:
        st.download_button(
            "⬇️ Export memories (JSON)",
            data=store.export_json(),
            file_name=f"memories_{profile}.json",
            mime="application/json",
            use_container_width=True,
        )
    with right:
        st.checkbox("I understand this deletes ALL memories in this profile", key="confirm_clear")
        if st.button("Delete all memories", disabled=not st.session_state.confirm_clear,
                     use_container_width=True):
            try:
                removed = store.clear()
                st.session_state.messages = []
                st.success(f"Deleted {removed} memories.")
                st.rerun()
            except MemoryStoreError as exc:
                st.error(str(exc))
