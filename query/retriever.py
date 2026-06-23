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


def retrieve_bilingual(
    original_question: str,
    english_question: str,
    k: int = TOP_K,
) -> list[Document]:
    """
    Retrieve chunks using BOTH the original-language question AND the
    English translation, then merge and deduplicate.

    Why: The multilingual E5 embedding model maps EN and JA into
    overlapping but NOT identical vector spaces. A single query in one
    language biases toward chunks stored in that same language. By
    querying twice we guarantee coverage of both languages' chunks.

    If original == english (user typed English), we just do a single
    retrieval to avoid wasting time.
    """
    retriever = get_retriever(k)

    # ── If both are the same, single retrieval is enough ──────────────
    if original_question.strip().lower() == english_question.strip().lower():
        return retriever.invoke(english_question)

    # ── Two retrievals: original language + English ───────────────────
    docs_original = retriever.invoke(original_question)
    docs_english  = retriever.invoke(english_question)

    # ── Merge + deduplicate by page_content ───────────────────────────
    seen = set()
    merged: list[Document] = []

    for doc in docs_english + docs_original:
        # Use first 200 chars as dedup key (avoids exact-match issues
        # from minor whitespace differences)
        key = doc.page_content[:200].strip()
        if key not in seen:
            seen.add(key)
            merged.append(doc)

    # Cap at 2*k to avoid feeding too much to the relevance filter
    return merged[:k * 2]