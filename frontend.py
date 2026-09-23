import streamlit as st
import requests
import secrets


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "https://nexarag-puuh.onrender.com"

st.set_page_config(
    page_title="NexaRAG",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    :root {
        --gold: #f1c76b;
        --cyan: #00d9ff;
        --bg: #0a0a0e;
        --surface: #151520;
        --border: #2a2a33;
        --text: #f5f5f8;
        --muted: #a0a0a8;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0a0e 0%, #0f0f14 100%);
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f14 0%, #0a0a0e 100%);
        border-right: 1px solid var(--border);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .brand {
        padding: 20px;
        background: linear-gradient(
            135deg,
            rgba(241,199,107,0.08),
            rgba(0,217,255,0.08)
        );
        border: 1px solid var(--border);
        border-radius: 14px;
        margin-bottom: 25px;
    }

    .brand-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 0.5px;
        background: linear-gradient(135deg, #f1c76b, #00d9ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 6px;
    }

    .brand-subtitle {
        font-size: 12px;
        letter-spacing: 1.5px;
        color: var(--muted);
        text-transform: uppercase;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] button[kind="secondary"] {
        border-radius: 10px;
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        border-color: var(--gold) !important;
    }

    .chat-label {
        color: var(--muted);
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 22px;
        margin-bottom: 10px;
        font-weight: 700;
    }

    .main-title {
        text-align: center;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -1.5px;
        background: linear-gradient(135deg, #f1c76b, #00d9ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 30px;
        margin-bottom: 12px;
    }

    .main-subtitle {
        text-align: center;
        color: var(--muted);
        font-size: 15px;
        margin-bottom: 30px;
    }

    /* ========================================================
       CHAT MESSAGE STYLE

       Positioning is handled by Streamlit's horizontal
       containers. No fragile :has() alignment hacks.
    ======================================================== */

    [data-testid="stChatMessage"] {
        width: fit-content !important;
        max-width: 100% !important;
        padding: 0 !important;
        margin: 4px 0 !important;
    }

    /* AI: clean ChatGPT-style response */
    [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarAssistant"]
    ) > div:last-child {
        background: transparent !important;
        border: none !important;
        padding: 8px 12px !important;
    }

    /* User: compact dark bubble */
    [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarUser"]
    ) > div:last-child {
        background: #2f2f2f !important;
        border: none !important;
        border-radius: 18px !important;
        padding: 10px 16px !important;
        box-shadow: none !important;
    }

    /* Hide the default user avatar */
    [data-testid="stChatMessageAvatarUser"] {
        display: none !important;
    }

    [data-testid="stChatInput"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
    }

    [data-testid="stChatInput"] textarea {
        background: transparent;
        color: var(--text);
    }

    .document-bar {
        background: rgba(21, 21, 32, 0.92);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 8px 12px;
        margin: 8px 0 6px 0;
    }

    .document-bar-title {
        color: var(--muted);
        font-size: 11px;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .document-item {
        color: var(--text);
        font-size: 13px;
        padding: 3px 0;
    }

    /* Floating document button */
    .doc-float-label {
        color: var(--text);
        font-size: 13px;
        font-weight: 700;
        padding: 2px 0 6px 0;
    }

    .doc-item-small {
        color: var(--text);
        font-size: 12px;
        padding: 5px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .doc-item-small:last-child {
        border-bottom: none;
    }

    .upload-status {
        color: #8ee6a8;
        font-size: 12px;
        margin-top: 8px;
    }

    .stAlert {
        border-radius: 12px;
    }

    @media (max-width: 768px) {
        .main-title {
            font-size: 28px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if "chats" not in st.session_state:
    st.session_state.chats = None

if "upload_status" not in st.session_state:
    st.session_state.upload_status = None


# ============================================================
# NEXARAG SESSION
# ============================================================

if "nexa_session_id" not in st.session_state:
    st.session_state.nexa_session_id = secrets.token_urlsafe(32)

REQUEST_HEADERS = {
    "X-Nexa-Session": st.session_state.nexa_session_id
}


# ============================================================
# BACKEND HELPERS
# ============================================================

def get_chats():
    """Get all chats, with a small retry for startup/backend timing."""
    for _ in range(3):
        try:
            response = requests.get(
                f"{API_URL}/chats",
                headers=REQUEST_HEADERS,
                timeout=10
            )
            if response.status_code == 200:
                chats = response.json().get("chats", [])
                st.session_state.chats = chats
                return chats
        except requests.RequestException:
            continue

    # Do not replace an already-loaded list with an empty list just because
    # the backend was temporarily unavailable.
    if st.session_state.chats is not None:
        return st.session_state.chats

    return []


def create_chat():
    try:
        response = requests.post(
            f"{API_URL}/chat/create",
            headers=REQUEST_HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.chat_id = data["chat_id"]
            st.session_state.messages = []
            # Refresh the sidebar list immediately after creating a chat.
            st.session_state.chats = None
            st.rerun()
        else:
            st.error("Unable to create chat.")
    except requests.RequestException:
        st.error("Unable to connect to the backend.")


def load_history(chat_id):
    try:
        response = requests.get(
            f"{API_URL}/chat/{chat_id}/history",
            headers=REQUEST_HEADERS,
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("history", [])
    except requests.RequestException:
        pass
    return []


def upload_document(chat_id, uploaded_file):
    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        response = requests.post(
            f"{API_URL}/chat/{chat_id}/upload",
            headers=REQUEST_HEADERS,
            files=files,
            timeout=120
        )

        if response.status_code == 200:
            return True

        if response.status_code == 409:
            st.warning(
                f"'{uploaded_file.name}' is already in this chat."
            )
            return False

        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text

        st.error(f"Upload failed: {detail}")
        return False

    except requests.RequestException as error:
        st.error(f"Unable to upload document: {error}")
        return False


def get_documents(chat_id):
    """Get the PDFs currently attached to the selected chat."""
    try:
        response = requests.get(
            f"{API_URL}/chat/{chat_id}/documents",
            headers=REQUEST_HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get("documents", [])

    except requests.RequestException:
        pass

    return []


def ask_question(chat_id, question):
    """Send a question to FastAPI. The model call happens in the backend."""
    try:
        payload = {"question": question}

        if st.session_state.api_key.strip():
            payload["api_key"] = st.session_state.api_key.strip()

        response = requests.post(
            f"{API_URL}/chat/{chat_id}/ask",
            headers=REQUEST_HEADERS,
            json=payload,
            timeout=180
        )

        if response.status_code == 200:
            return response.json().get("answer")

        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text

        if (
            response.status_code == 429
            or "quota" in str(detail).lower()
            or "429" in str(detail)
        ):
            st.warning(
                "API quota exceeded. Provide your own API key in Settings."
            )
            return None

        st.error(f"Request failed: {detail}")
        return None

    except requests.Timeout:
        st.error("The request took too long. Please try again.")
        return None

    except requests.RequestException as error:
        st.error(f"Unable to connect to backend: {error}")
        return None


def rename_chat(chat_id, new_name):
    try:
        response = requests.patch(
            f"{API_URL}/chat/{chat_id}/rename",
            headers=REQUEST_HEADERS,
            json={"name": new_name},
            timeout=10
        )

        if response.status_code == 200:
            return True

        try:
            detail = response.json().get("detail")
        except Exception:
            detail = response.text
        st.error(detail)

    except requests.RequestException:
        st.error("Unable to rename chat.")

    return False


def delete_chat(chat_id):
    try:
        response = requests.delete(
            f"{API_URL}/chat/{chat_id}",
            headers=REQUEST_HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            return True

        st.error("Unable to delete chat.")

    except requests.RequestException:
        st.error("Unable to connect to backend.")

    return False


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-title">◈ NexaRAG</div>
            <div class="brand-subtitle">Intelligent Workspace</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "＋  New conversation",
        use_container_width=True
    ):
        create_chat()

    st.markdown(
        '<div class="chat-label">Conversations</div>',
        unsafe_allow_html=True
    )

    chats = get_chats()

    if chats:
        for chat in chats:
            listed_chat_id = chat["id"]
            chat_name = chat["name"]
            is_current = st.session_state.chat_id == listed_chat_id

            label = (
                f"●  {chat_name}"
                if is_current
                else f"   {chat_name}"
            )

            if st.button(
                label,
                key=f"chat_{listed_chat_id}",
                use_container_width=True
            ):
                st.session_state.chat_id = listed_chat_id
                st.session_state.messages = load_history(listed_chat_id)
                st.rerun()
    else:
        st.caption("No conversations yet.")

    if st.session_state.chat_id is not None:
        st.divider()

        st.markdown(
            '<div class="chat-label">Current Conversation</div>',
            unsafe_allow_html=True
        )

        rename_name = st.text_input(
            "Rename",
            value="",
            placeholder="New name",
            key="rename_input",
            label_visibility="collapsed"
        )

        if st.button("Rename", use_container_width=True):
            if rename_name.strip():
                if rename_chat(
                    st.session_state.chat_id,
                    rename_name.strip()
                ):
                    st.toast("✓ Renamed")
                    st.rerun()
            else:
                st.warning("Enter a name.")

        if st.button(
            "Delete conversation",
            use_container_width=True
        ):
            if delete_chat(st.session_state.chat_id):
                st.session_state.chat_id = None
                st.session_state.messages = []
                st.rerun()

    st.divider()

    if st.button("⚙  Settings", use_container_width=True):
        st.session_state.show_settings = (
            not st.session_state.show_settings
        )
        st.rerun()

    if st.session_state.show_settings:
        st.markdown("### API Configuration")
        st.caption("Provide your own Gemini API key.")

        api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="Enter your API key",
            label_visibility="collapsed"
        )

        st.session_state.api_key = api_key

        if api_key.strip():
            st.success("✓ Using your API key")
        else:
            st.info("Using default API key")


# ============================================================
# NO CHAT SELECTED
# ============================================================

if st.session_state.chat_id is None:

    st.markdown(
        """
        <div class="main-title">NexaRAG</div>
        <div class="main-subtitle">
            Upload documents, ask questions, and work with your knowledge in one place.
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "＋ Create new conversation",
            use_container_width=True
        ):
            create_chat()

        st.info("👈 Select a conversation to continue")

    st.stop()


# ============================================================
# CURRENT CHAT
# ============================================================

chat_id = st.session_state.chat_id

if not st.session_state.messages:
    st.session_state.messages = load_history(chat_id)

current_chat_name = "Knowledge Assistant"

for chat in chats:
    if chat["id"] == chat_id:
        current_chat_name = chat["name"]
        break

st.markdown(
    f"""
    <div class="main-title">{current_chat_name}</div>
    <div class="main-subtitle">Ask anything about your documents.</div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message.get("role")
    content = message.get("content", "")

    if role == "assistant":

        # AI -> LEFT
        with st.container(
            horizontal=True,
            horizontal_alignment="left",
            gap="small"
        ):
            with st.chat_message(
                "assistant",
                width="content"
            ):
                st.write(content)

    elif role == "user":

        # USER -> RIGHT
        with st.container(
            horizontal=True,
            horizontal_alignment="right",
            gap="small"
        ):
            with st.chat_message(
                "user",
                width="content"
            ):
                st.write(content)


# ============================================================
# DOCUMENT BUTTON + CHAT INPUT
# ============================================================

documents = get_documents(chat_id)

# Keep the document viewer hidden by default. The popover is attached
# to the chat input area, so it remains available without becoming
# part of the conversation history.
with st.popover(
    f"📎 {len(documents)}" if documents else "📎",
    use_container_width=False
):
    st.markdown(
        '<div class="doc-float-label">Attached documents</div>',
        unsafe_allow_html=True
    )

    if documents:
        for document in documents:
            size_kb = document.get("size", 0) / 1024
            st.markdown(
                f'<div class="doc-item-small">📄 <b>{document["name"]}</b><br>· {size_kb:.1f} KB</div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("No documents uploaded to this chat.")

    if st.session_state.upload_status:
        st.markdown(
            f'<div class="upload-status">✓ {st.session_state.upload_status}</div>',
            unsafe_allow_html=True
        )

submission = st.chat_input(
    "Message your knowledge assistant...",
    accept_file=True,
    file_type=["pdf"],
    key=f"chat_input_{chat_id}"
)


# ============================================================
# PROCESS SUBMISSION
# ============================================================

if submission:

    question = submission.text.strip()
    uploaded_files = submission.files

    # --------------------------------------------------------
    # UPLOAD PDF FIRST
    # --------------------------------------------------------

    if uploaded_files:

        for uploaded_file in uploaded_files:

            with st.spinner(
                f"Adding {uploaded_file.name}..."
            ):

                success = upload_document(
                    chat_id,
                    uploaded_file
                )

            if success:
                st.session_state.upload_status = (
                    f"{uploaded_file.name} uploaded successfully"
                )

    # --------------------------------------------------------
    # ASK QUESTION
    # --------------------------------------------------------

    if question:

        # The upload confirmation is no longer needed once the user
        # continues with a new question.
        st.session_state.upload_status = None

        # User -> RIGHT
        with st.container(
            horizontal=True,
            horizontal_alignment="right",
            gap="small"
        ):
            with st.chat_message(
                "user",
                width="content"
            ):
                st.write(question)

        # AI -> LEFT
        with st.container(
            horizontal=True,
            horizontal_alignment="left",
            gap="small"
        ):
            with st.chat_message(
                "assistant",
                width="content"
            ):

                with st.spinner("Thinking..."):

                    answer = ask_question(
                        chat_id,
                        question
                    )

                if answer is not None:
                    st.write(answer)

        # Refresh history
        st.session_state.messages = load_history(
            chat_id
        )

    # --------------------------------------------------------
    # FILE ONLY
    # --------------------------------------------------------

    elif uploaded_files:

        st.session_state.messages = load_history(
            chat_id
        )

        st.rerun()
