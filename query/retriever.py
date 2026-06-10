import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from ingestion.embedder import get_vectorstore
from config import TOP_K


def get_retriever():
    """
    Return a configured ChromaDB retriever.
    Uses multilingual-e5-large embeddings so Japanese and English
    questions both retrieve correctly regardless of source language.
    """
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )


def retrieve_chunks(question: str) -> list[Document]:
    """
    Retrieve top-K semantically relevant chunks for a question.
    Works equally for English and Japanese questions.
    No LLM call happens here — pure vector similarity search.
    """
    retriever = get_retriever()
    return retriever.invoke(question)