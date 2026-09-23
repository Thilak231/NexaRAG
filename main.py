from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from pydantic import BaseModel

from langchain_google_genai.chat_models import (
    ChatGoogleGenerativeAIError
)

import shutil
import os

from rag.chat_service import (
    create_new_chat,
    get_all_chats,
    remove_chat,
    upload_document,
    ask_question,
    get_chat_history,
    get_documents,
    delete_document,
    rename_existing_chat
)

from rag.chat_manager import get_chat_path


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="NexaRag",
    description="Multi Chat RAG Backend",
    version="1.0"
)


# =========================================================
# REQUEST MODELS
# =========================================================

class QuestionRequest(BaseModel):

    question: str

    # Optional user-provided Gemini API key.
    #
    # None means:
    # use the application's default API key.

    api_key: str | None = None


class RenameChatRequest(BaseModel):

    name: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "NexaRag Backend Running"
    }


# =========================================================
# CREATE CHAT
# =========================================================

@app.post("/chat/create")
def create_chat():

    return create_new_chat()


# =========================================================
# LIST CHATS
# =========================================================

@app.get("/chats")
def list_all_chats():

    return get_all_chats()


# =========================================================
# DELETE CHAT
# =========================================================

@app.delete("/chat/{chat_id}")
def delete_existing_chat(
    chat_id: int
):

    return remove_chat(
        chat_id
    )


# =========================================================
# RENAME CHAT
# =========================================================

@app.patch(
    "/chat/{chat_id}/rename"
)
def rename_existing_chat_endpoint(
    chat_id: int,
    request: RenameChatRequest
):

    result = rename_existing_chat(
        chat_id,
        request.name
    )

    if "error" in result:

        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result


# =========================================================
# UPLOAD PDF
# =========================================================

@app.post(
    "/chat/{chat_id}/upload"
)
def upload_pdf(
    chat_id: int,
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # Check chat
    # -----------------------------------------------------

    chat_path = get_chat_path(
        chat_id
    )

    if chat_path is None:

        raise HTTPException(
            status_code=404,
            detail="Chat not found."
        )

    # -----------------------------------------------------
    # Check file type
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="File name is missing."
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # -----------------------------------------------------
    # Documents directory
    # -----------------------------------------------------

    documents_path = os.path.join(
        chat_path,
        "documents"
    )

    os.makedirs(
        documents_path,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Sanitize filename
    # -----------------------------------------------------

    filename = os.path.basename(
        file.filename
    )

    pdf_path = os.path.join(
        documents_path,
        filename
    )

    # -----------------------------------------------------
    # Duplicate document check
    # -----------------------------------------------------

    if os.path.exists(
        pdf_path
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "This document already exists "
                "in the chat."
            )
        )

    # -----------------------------------------------------
    # Save and process PDF
    # -----------------------------------------------------

    try:

        with open(
            pdf_path,
            "wb"
        ) as pdf:

            shutil.copyfileobj(
                file.file,
                pdf
            )

        result = upload_document(
            chat_id,
            pdf_path
        )

        return result

    except Exception as error:

        # -------------------------------------------------
        # Rollback:
        #
        # If embedding / FAISS creation fails,
        # remove the PDF so we don't leave a document
        # that isn't actually indexed.
        # -------------------------------------------------

        if os.path.exists(
            pdf_path
        ):

            os.remove(
                pdf_path
            )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# ASK QUESTION
# =========================================================

@app.post(
    "/chat/{chat_id}/ask"
)
def ask_chat_question(
    chat_id: int,
    request: QuestionRequest
):

    # -----------------------------------------------------
    # Validate question
    # -----------------------------------------------------

    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = ask_question(
            chat_id,
            request.question,
            request.api_key
        )

        # -------------------------------------------------
        # Chat service returned an application error
        # -------------------------------------------------

        if "error" in result:

            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )

        return result

    # -----------------------------------------------------
    # Gemini quota / API errors
    # -----------------------------------------------------

    except ChatGoogleGenerativeAIError as error:

        error_message = str(
            error
        )

        if "RESOURCE_EXHAUSTED" in error_message:

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded. "
                    "Please switch to your own Gemini "
                    "API key in Settings or wait for "
                    "the quota to reset."
                )
            )

        raise HTTPException(
            status_code=502,
            detail="Gemini API request failed."
        )

    # -----------------------------------------------------
    # Preserve FastAPI HTTP errors
    # -----------------------------------------------------

    except HTTPException:

        raise

    # -----------------------------------------------------
    # Unexpected errors
    # -----------------------------------------------------

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Internal server error."
        )


# =========================================================
# CHAT HISTORY
# =========================================================

@app.get(
    "/chat/{chat_id}/history"
)
def chat_history(
    chat_id: int
):

    result = get_chat_history(
        chat_id
    )

    if "error" in result:

        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result


# =========================================================
# CHAT DOCUMENTS
# =========================================================

@app.get(
    "/chat/{chat_id}/documents"
)
def chat_documents(
    chat_id: int
):

    result = get_documents(
        chat_id
    )

    if "error" in result:

        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result


# =========================================================
# DELETE DOCUMENT
# =========================================================

@app.delete(
    "/chat/{chat_id}/documents/{filename}"
)
def remove_document(
    chat_id: int,
    filename: str
):

    result = delete_document(
        chat_id,
        filename
    )

    if "error" in result:

        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result