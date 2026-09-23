from rag.chains import (
    create_document_chain,
    create_retrieval_pipeline
)

from rag.config import llm
from rag.chat_manager import create_chat, open_chat
from rag.vector_store import (
    vector_db_exists,
    create_vector_db,
    upload_pdf,
    load_vector_db
)

# --------------------- CHAT SELECTION ---------------------

while True:

    print("\n========== NexaRag ==========")
    print("1. Create New Chat")
    print("2. Open Existing Chat")
    print("3. Exit")

    choice = input("\nEnter your choice: ")

    if choice == "1":

        chat_path = create_chat()
        print(f"\nChat created successfully!\n{chat_path}")
        break

    elif choice == "2":

        chat_id = input("Enter chat number: ")

        chat_path = open_chat(chat_id)

        if chat_path is None:
            print("❌ Chat not found.")
            continue

        break

    elif choice == "3":

        exit()

    else:

        print("❌ Invalid choice.")


# --------------------- PROMPT ---------------------

prompt = ChatPromptTemplate.from_template("""
You are an intelligent AI assistant.

Answer the user's question using the retrieved document context whenever it is relevant.

Rules:

1. If the uploaded documents completely answer the question,
   answer using the documents.

2. If the uploaded documents only partially answer the question,
   complete the remaining answer using your own knowledge.

3. If the uploaded documents do not contain the answer,
   answer using your own knowledge.

4. Whenever you use information that is NOT from the uploaded
   documents, clearly mention:

   "The uploaded documents do not contain this information.
    The following answer is based on my general knowledge."

Context:
{context}

Question:
{input}
""")

document_chain = create_stuff_documents_chain(
    llm,
    prompt
)


# --------------------- LOAD VECTOR DATABASE ---------------------

if vector_db_exists(chat_path):

    vector_db = load_vector_db(chat_path)

    retriever = vector_db.as_retriever(
        search_kwargs={"k": 3}
    )

    retrieval_chain = create_retrieval_chain(
        retriever,
        document_chain
    )

else:

    vector_db = None
    retrieval_chain = None


# --------------------- CHAT LOOP ---------------------

while True:

    question = input("\nYou : ")

    if question.lower() == "exit":
        break


    elif question.lower() == "upload":

        pdf_path = input("Enter PDF path: ")

        if vector_db is None:

            vector_db = create_vector_db(
                pdf_path,
                chat_path
            )

        else:

            upload_pdf(
                pdf_path,
                vector_db,
                chat_path
            )

        retriever = vector_db.as_retriever(
            search_kwargs={"k": 3}
        )

        retrieval_chain = create_retrieval_chain(
            retriever,
            document_chain
        )

        print("✅ PDF uploaded successfully.")

        continue


    # ---------- PURE LLM MODE ----------

    if retrieval_chain is None:

        response = llm.invoke(question)

        print("\nAI :", response.content)


    # ---------- RAG MODE ----------

    else:

        response = retrieval_chain.invoke(
            {
                "input": question
            }
        )

        print("\nAI :", response["answer"])