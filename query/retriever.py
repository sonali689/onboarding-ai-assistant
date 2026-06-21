import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from ingestion.embedder import get_vectorstore
from config import TOP_K, MMR_FETCH_K, MMR_LAMBDA


def get_retriever(k: int = TOP_K):
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": MMR_FETCH_K,
            "lambda_mult": MMR_LAMBDA,
        },
    )


def retrieve_chunks(question: str, k: int = TOP_K) -> list[Document]:
    retriever = get_retriever(k)
    return retriever.invoke(question)