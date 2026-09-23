import json
import os
import shutil
import hashlib

from rag.session import get_current_user


CHATS_FOLDER = "chats"


# ====================================================
# User Folder
# ====================================================

def get_user_folder():

    user_id = get_current_user()

    user_hash = hashlib.sha256(
        user_id.encode("utf-8")
    ).hexdigest()[:32]

    return os.path.join(
        CHATS_FOLDER,
        user_hash
    )


# ====================================================
# Chat Metadata
# ====================================================

def get_metadata_path(chat_path):

    return os.path.join(
        chat_path,
        "chat_metadata.json"
    )


def get_chat_name(chat_path):

    metadata_path = get_metadata_path(
        chat_path
    )

    if not os.path.exists(metadata_path):

        return os.path.basename(
            chat_path
        )

    try:

        with open(
            metadata_path,
            "r",
            encoding="utf-8"
        ) as file:

            metadata = json.load(file)

        return metadata.get(
            "name",
            os.path.basename(chat_path)
        )

    except Exception:

        return os.path.basename(
            chat_path
        )


def save_chat_name(
    chat_path,
    name
):

    metadata_path = get_metadata_path(
        chat_path
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "name": name
            },
            file,
            indent=4,
            ensure_ascii=False
        )


# ====================================================
# Create Chat
# ====================================================

def create_chat():

    user_folder = get_user_folder()

    os.makedirs(
        user_folder,
        exist_ok=True
    )

    chat_folders = os.listdir(
        user_folder
    )

    max_chat_id = 0

    for chat in chat_folders:

        parts = chat.split("_")

        if (
            len(parts) == 2
            and parts[1].isdigit()
        ):

            chat_id = int(
                parts[1]
            )

            if chat_id > max_chat_id:

                max_chat_id = chat_id

    next_chat_id = max_chat_id + 1

    chat_name = f"chat_{next_chat_id:03d}"

    chat_path = os.path.join(
        user_folder,
        chat_name
    )

    os.makedirs(chat_path)

    os.makedirs(
        os.path.join(
            chat_path,
            "database"
        )
    )

    os.makedirs(
        os.path.join(
            chat_path,
            "documents"
        )
    )

    # Human-readable display name
    save_chat_name(
        chat_path,
        "New Chat"
    )

    return next_chat_id


# ====================================================
# Get Chat Path
# ====================================================

def get_chat_path(chat_id):

    user_folder = get_user_folder()

    chat_name = f"chat_{int(chat_id):03d}"

    chat_path = os.path.join(
        user_folder,
        chat_name
    )

    if os.path.exists(chat_path):

        return chat_path

    return None


# ====================================================
# Rename Chat
# ====================================================

def rename_chat(
    chat_id,
    new_name
):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return False

    new_name = new_name.strip()

    if not new_name:

        return False

    save_chat_name(
        chat_path,
        new_name
    )

    return True


# ====================================================
# List Chats
# ====================================================

def list_chats():

    user_folder = get_user_folder()

    if not os.path.exists(
        user_folder
    ):

        return []

    chat_folders = []

    for folder in os.listdir(
        user_folder
    ):

        chat_path = os.path.join(
            user_folder,
            folder
        )

        if (
            os.path.isdir(chat_path)
            and folder.startswith("chat_")
        ):

            chat_folders.append(
                folder
            )

    chat_folders.sort()

    return chat_folders


# ====================================================
# Delete Chat
# ====================================================

def delete_chat(chat_id):

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        return False

    shutil.rmtree(
        chat_path
    )

    return True