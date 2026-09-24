from dotenv import load_dotenv

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

load_dotenv()


# Application default LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)


# Application default embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)


def create_llm(api_key=None):

    if not api_key:
        return llm

    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=api_key
    )