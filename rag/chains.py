from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.combine_documents import (
    create_stuff_documents_chain
)
from langchain_classic.chains import (
    create_retrieval_chain
)


def create_document_chain(llm):

    prompt = ChatPromptTemplate.from_template("""
You are a helpful, intelligent, and natural AI assistant.

Your personality should feel conversational and human
rather than robotic. You can show appropriate emotions
such as enthusiasm, empathy, curiosity, or humor when
appropriate.

Be concise when a simple answer is enough, but explain
things properly when the user needs more detail.

You have access to information retrieved from the user's
uploaded documents.

Use the following rules:

1. If the uploaded documents contain the answer, prioritize
   the information from those documents.

2. If the documents partially answer the question, use the
   document information and supplement missing parts with
   your general knowledge when appropriate.

3. If the documents do not contain the requested information,
   answer naturally using your general knowledge.

4. Do not pretend that general knowledge came from the
   uploaded documents.

5. When the answer comes entirely or substantially from
   general knowledge because the documents do not contain
   the requested information, make that clear naturally.

6. Never invent information from the uploaded documents.

7. If the user asks a casual question that does not require
   document retrieval, answer naturally.

Context:
{context}

User:
{input}

Answer naturally:
""")

    return create_stuff_documents_chain(
        llm,
        prompt
    )


def create_retrieval_pipeline(vector_db, llm):

    retriever = vector_db.as_retriever(
        search_kwargs={"k": 3}
    )

    document_chain = create_document_chain(
        llm
    )

    return create_retrieval_chain(
        retriever,
        document_chain
    )