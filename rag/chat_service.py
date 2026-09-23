# ------------ Business Logic Layer ------------

import json
import os
import hashlib

from rag.chat_manager import (
    create_chat,
    get_chat_path,
    list_chats,
    delete_chat,
    get_chat_name,
    rename_chat
)

from rag.vector_store import (
    vector_db_exists,
    create_vector_db,
    load_vector_db,
    upload_pdf,
    rebuild_vector_db
)

from rag.chains import create_retrieval_pipeline
from rag.config import llm, create_llm


# =========================================================
# CACHE
# =========================================================

# Stores loaded FAISS databases and retrieval chains.
#
# Cache key:
#
#     (chat_id, api_key_fingerprint)
#
# This allows the same chat to use either:
#     - Application Default LLM
#     - User's Gemini API key
#
# without mixing the two configurations.

_CHAT_CACHE = {}


def get_key_fingerprint(api_key):
    """
    Create a non-reversible fingerprint of the API key.

    The actual API key is never used directly as the
    cache dictionary key.
    """

    if not api_key:
        return "default"

    return hashlib.sha256(
        api_key.encode()
    ).hexdigest()


def clear_chat_cache(chat_id):
    """
    Clear all cached data belonging to a chat.

    Called when:
        - A document is uploaded
        - A document is deleted
        - A chat is deleted
    """

    keys_to_remove = [
        key
        for key in _CHAT_CACHE
        if key[0] == chat_id
    ]

    for key in keys_to_remove:
        del _CHAT_CACHE[key]


def get_cached_retrieval_chain(
    chat_id,
    chat_path,
    api_key=None
):
    """
    Return a cached retrieval chain for the chat.

    If the chain does not exist in memory:
        1. Load FAISS from disk
        2. Create the selected LLM
        3. Create the retrieval pipeline
        4. Store it in memory
    """

    key_fingerprint = get_key_fingerprint(
        api_key
    )

    cache_key = (
        chat_id,
        key_fingerprint
    )

    # -----------------------------------------------------
    # CACHE HIT
    # -----------------------------------------------------

    if cache_key in _CHAT_CACHE:

        return _CHAT_CACHE[
            cache_key
        ]["retrieval_chain"]

    # -----------------------------------------------------
    # CACHE MISS
    # -----------------------------------------------------

    vector_db = load_vector_db(
        chat_path
    )

    selected_llm = create_llm(
        api_key
    )

    retrieval_chain = create_retrieval_pipeline(
        vector_db,
        selected_llm
    )

    # Store in memory
    _CHAT_CACHE[cache_key] = {
        "vector_db": vector_db,
        "retrieval_chain": retrieval_chain
    }

    return retrieval_chain


# =========================================================
# HISTORY
# =========================================================

def get_history_path(chat_path):
    return os.path.join(
        chat_path,
        "history.json"
    )


def load_history(chat_path):

    history_path = get_history_path(
        chat_path
    )

    if not os.path.exists(history_path):
        return []

    try:

        with open(
            history_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return []


def save_history(
    chat_path,
    history
):

    history_path = get_history_path(
        chat_path
    )

    with open(
        history_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            indent=4,
            ensure_ascii=False
        )


def add_message(
    chat_path,
    role,
    content
):

    history = load_history(
        chat_path
    )

    history.append({
        "role": role,
        "content": content
    })

    save_history(
        chat_path,
        history
    )


# =========================================================
# RESPONSE HANDLING
# =========================================================

def extract_response_text(response):
    """
    Convert an LLM response into a normal string.

    Handles both:
        - string content
        - list/block content
    """

    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        text_parts = []

        for block in content:

            if isinstance(block, str):

                text_parts.append(
                    block
                )

            elif isinstance(block, dict):

                text = block.get(
                    "text"
                )

                if text:
                    text_parts.append(
                        text
                    )

        return "\n".join(
            text_parts
        ).strip()

    return str(content)


# =========================================================
# CREATE CHAT
# =========================================================

def create_new_chat():

    chat_id = create_chat()

    chat_path = get_chat_path(
        chat_id
    )

    save_history(
        chat_path,
        []
    )

    return {
        "chat_id": chat_id,
        "message": "Chat created successfully."
    }


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

def upload_document(
    chat_id,
    pdf_path
):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return {
            "error": "Chat not found."
        }

    # -----------------------------------------------------
    # Existing vector database
    # -----------------------------------------------------

    if vector_db_exists(
        chat_path
    ):

        vector_db = load_vector_db(
            chat_path
        )

        upload_pdf(
            pdf_path,
            vector_db,
            chat_path
        )

    # -----------------------------------------------------
    # First document
    # -----------------------------------------------------

    else:

        create_vector_db(
            pdf_path,
            chat_path
        )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # The FAISS database has changed.
    #
    # The cached retrieval chain contains the OLD
    # vector database, so invalidate the cache.
    # -----------------------------------------------------

    clear_chat_cache(
        chat_id
    )

    return {
        "message": "PDF uploaded successfully."
    }


# =========================================================
# ASK QUESTION
# =========================================================

def ask_question(
    chat_id,
    question,
    api_key=None
):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return {
            "error": "Chat not found."
        }

    # -----------------------------------------------------
    # Save user message
    # -----------------------------------------------------

    add_message(
        chat_path,
        "user",
        question
    )

    # -----------------------------------------------------
    # RAG MODE
    #
    # Chat contains uploaded documents.
    # -----------------------------------------------------

    if vector_db_exists(
        chat_path
    ):

        retrieval_chain = get_cached_retrieval_chain(
            chat_id,
            chat_path,
            api_key
        )

        response = retrieval_chain.invoke({
            "input": question
        })

        answer = response["answer"]

        # -------------------------------------------------
        # Convert answer to string if necessary
        # -------------------------------------------------

        if not isinstance(answer, str):

            if isinstance(answer, list):

                text_parts = []

                for block in answer:

                    if isinstance(
                        block,
                        str
                    ):

                        text_parts.append(
                            block
                        )

                    elif isinstance(
                        block,
                        dict
                    ):

                        text = block.get(
                            "text"
                        )

                        if text:

                            text_parts.append(
                                text
                            )

                answer = "\n".join(
                    text_parts
                ).strip()

            else:

                answer = str(
                    answer
                )

    # -----------------------------------------------------
    # GENERAL LLM MODE
    #
    # Chat has no uploaded documents.
    # -----------------------------------------------------

    else:

        selected_llm = create_llm(
            api_key
        )

        response = selected_llm.invoke(
            question
        )

        answer = extract_response_text(
            response
        )

    # -----------------------------------------------------
    # Save assistant response
    # -----------------------------------------------------

    add_message(
        chat_path,
        "assistant",
        answer
    )

    return {
        "answer": answer
    }


# =========================================================
# LIST ALL CHATS
# =========================================================

def get_all_chats():

    chat_folders = list_chats()

    chats = []

    for folder in chat_folders:

        chat_id = int(
            folder.split("_")[1]
        )

        chat_path = get_chat_path(
            chat_id
        )

        chats.append({
            "id": chat_id,
            "name": get_chat_name(
                chat_path
            )
        })

    return {
        "chats": chats
    }


# =========================================================
# RENAME CHAT
# =========================================================

def rename_existing_chat(
    chat_id,
    new_name
):

    if not new_name.strip():

        return {
            "error": "Chat name cannot be empty."
        }

    if len(
        new_name.strip()
    ) > 60:

        return {
            "error": (
                "Chat name cannot exceed 60 characters."
            )
        }

    renamed = rename_chat(
        chat_id,
        new_name
    )

    if not renamed:

        return {
            "error": "Chat not found."
        }

    return {
        "message": "Chat renamed successfully.",
        "name": new_name.strip()
    }


# =========================================================
# DELETE CHAT
# =========================================================

def remove_chat(chat_id):

    deleted = delete_chat(
        chat_id
    )

    if deleted:

        # The chat no longer exists,
        # so remove its cached objects.

        clear_chat_cache(
            chat_id
        )

        return {
            "message": "Chat deleted successfully."
        }

    return {
        "error": "Chat not found."
    }


# =========================================================
# GET CHAT HISTORY
# =========================================================

def get_chat_history(chat_id):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return {
            "error": "Chat not found."
        }

    return {
        "history": load_history(
            chat_path
        )
    }


# =========================================================
# GET DOCUMENTS
# =========================================================

def get_documents(chat_id):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return {
            "error": "Chat not found."
        }

    documents_path = os.path.join(
        chat_path,
        "documents"
    )

    documents = []

    if os.path.exists(
        documents_path
    ):

        for filename in os.listdir(
            documents_path
        ):

            if filename.lower().endswith(
                ".pdf"
            ):

                file_path = os.path.join(
                    documents_path,
                    filename
                )

                documents.append({
                    "name": filename,
                    "size": os.path.getsize(
                        file_path
                    )
                })

    return {
        "documents": documents
    }


# =========================================================
# DELETE DOCUMENT
# =========================================================

def delete_document(
    chat_id,
    filename
):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return {
            "error": "Chat not found."
        }

    documents_path = os.path.join(
        chat_path,
        "documents"
    )

    # Prevent path traversal
    filename = os.path.basename(
        filename
    )

    pdf_path = os.path.join(
        documents_path,
        filename
    )

    if not os.path.exists(
        pdf_path
    ):

        return {
            "error": "Document not found."
        }

    # -----------------------------------------------------
    # Delete PDF
    # -----------------------------------------------------

    os.remove(
        pdf_path
    )

    # -----------------------------------------------------
    # Rebuild FAISS using remaining PDFs
    # -----------------------------------------------------

    rebuild_vector_db(
        chat_path
    )

    # -----------------------------------------------------
    # The cached vector database is now outdated.
    # -----------------------------------------------------

    clear_chat_cache(
        chat_id
    )

    return {
        "message": "Document deleted successfully."
    }