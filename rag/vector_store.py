from langchain_community.vectorstores import FAISS
from rag.config import embeddings
from rag.document_loader import get_chunks

import os


# ----------------------------------------------------
# Check if Vector Database Exists
# ----------------------------------------------------

def vector_db_exists(chat_path):

    database_path = os.path.join(
        chat_path,
        "database"
    )

    return os.path.exists(
        os.path.join(
            database_path,
            "index.faiss"
        )
    )


# ----------------------------------------------------
# Create Vector Database
# ----------------------------------------------------

def create_vector_db(pdf_path, chat_path):

    chunks = get_chunks(pdf_path)

    vector_db = FAISS.from_documents(
        chunks,
        embeddings
    )

    save_vector_db(
        vector_db,
        chat_path
    )

    return vector_db


# ----------------------------------------------------
# Add PDF to Existing Vector Database
# ----------------------------------------------------

def upload_pdf(pdf_path, vector_db, chat_path):

    chunks = get_chunks(pdf_path)

    vector_db.add_documents(
        chunks
    )

    save_vector_db(
        vector_db,
        chat_path
    )


# ----------------------------------------------------
# Load Vector Database
# ----------------------------------------------------

def load_vector_db(chat_path):

    database_path = os.path.join(
        chat_path,
        "database"
    )

    vector_db = FAISS.load_local(
        database_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_db


# ----------------------------------------------------
# Save Vector Database
# ----------------------------------------------------

def save_vector_db(vector_db, chat_path):

    database_path = os.path.join(
        chat_path,
        "database"
    )

    os.makedirs(
        database_path,
        exist_ok=True
    )

    vector_db.save_local(
        database_path
    )


# ----------------------------------------------------
# Rebuild Vector Database
# ----------------------------------------------------
# Used when a document is deleted.
#
# Instead of trying to remove individual vectors
# from FAISS, we rebuild the index from the PDFs
# that are still present in the chat.
# ----------------------------------------------------

def rebuild_vector_db(chat_path):

    documents_path = os.path.join(
        chat_path,
        "documents"
    )

    pdf_files = []

    if os.path.exists(documents_path):

        for filename in os.listdir(documents_path):

            if filename.lower().endswith(".pdf"):

                pdf_files.append(
                    os.path.join(
                        documents_path,
                        filename
                    )
                )

    database_path = os.path.join(
        chat_path,
        "database"
    )

    # -----------------------------------------------
    # No documents remain
    # -----------------------------------------------

    if not pdf_files:

        if os.path.exists(database_path):

            for filename in os.listdir(database_path):

                file_path = os.path.join(
                    database_path,
                    filename
                )

                if os.path.isfile(file_path):

                    os.remove(file_path)

        return None

    # -----------------------------------------------
    # Process all remaining PDFs
    # -----------------------------------------------

    all_chunks = []

    for pdf_path in pdf_files:

        chunks = get_chunks(
            pdf_path
        )

        all_chunks.extend(
            chunks
        )

    # -----------------------------------------------
    # Create new FAISS index
    # -----------------------------------------------

    vector_db = FAISS.from_documents(
        all_chunks,
        embeddings
    )

    save_vector_db(
        vector_db,
        chat_path
    )

    return vector_db