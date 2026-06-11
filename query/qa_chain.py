import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama

from query.prompt_templates import BILINGUAL_PROMPT, GENERAL_KNOWLEDGE_PROMPT
from query.retriever import get_retriever, retrieve_chunks
from config import QWEN2_MODEL, OLLAMA_BASE_URL

# ── Cached instances ──────────────────────────────────────────────────────────
_llm       = None
_retriever = None

# Threshold — how many chunks must be retrieved to trust company data
MIN_RELEVANT_CHUNKS = 1

# If answer contains this, it means company data didn't have it
NOT_IN_CONTEXT_MARKER = "NOT_IN_CONTEXT"


def get_llm() -> Ollama:
    global _llm
    if _llm is None:
        _llm = Ollama(
            model=QWEN2_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
    return _llm


def format_docs(docs) -> str:
    """Format retrieved documents into a single context string."""
    parts = []
    for doc in docs:
        source    = doc.metadata.get("source", "")
        slide_num = doc.metadata.get("slide_number", "")
        subfolder = doc.metadata.get("subfolder", "")
        parts.append(
            f"[Source: {source} | Slide {slide_num} | {subfolder}]\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def is_relevant(docs, question: str) -> bool:
    """
    Decide if retrieved chunks are relevant enough to answer the question.
    Uses a simple scoring approach:
    - If no chunks retrieved → not relevant
    - If chunks retrieved but content is very short → not relevant
    - Otherwise → relevant, use company data
    """
    if not docs:
        return False

    # Combine all retrieved content
    combined = " ".join(doc.page_content for doc in docs).strip()

    # If retrieved content is very sparse, fall back to general knowledge
    if len(combined) < 100:
        return False

    return True


def ask_with_company_data(question: str, docs) -> str:
    """Run question against retrieved company data."""
    llm     = get_llm()
    context = format_docs(docs)

    chain = (
        BILINGUAL_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain.invoke({
        "context":  context,
        "question": question,
    })


def ask_with_general_knowledge(question: str) -> str:
    """Run question against Qwen2's general knowledge."""
    llm = get_llm()

    chain = (
        GENERAL_KNOWLEDGE_PROMPT
        | llm
        | StrOutputParser()
    )

    return chain.invoke({"question": question})


def ask(question: str) -> dict:
    """
    Main entry point for the query pipeline.

    Flow:
    1. Retrieve relevant chunks from ChromaDB
    2. Check if chunks actually answer the question
    3a. If yes → answer from company data with citations
    3b. If no  → answer from general knowledge, clearly labelled

    Returns:
        {
            "answer":       str,
            "sources":      list of source dicts,
            "source_type":  "company_data" or "general_knowledge"
        }
    """
    # Step 1 — Retrieve chunks
    docs = retrieve_chunks(question)

    # Step 2 — Check relevance
    if is_relevant(docs, question):
        # Step 3a — Try answering from company data
        raw_answer = ask_with_company_data(question, docs)

        # Step 3b — If model says NOT_IN_CONTEXT, fall back anyway
        if NOT_IN_CONTEXT_MARKER in raw_answer:
            answer      = ask_with_general_knowledge(question)
            source_type = "general_knowledge"
            sources     = []
        else:
            answer      = raw_answer
            source_type = "company_data"
            sources     = _build_sources(docs)
    else:
        # Step 3b — No relevant chunks, use general knowledge
        answer      = ask_with_general_knowledge(question)
        source_type = "general_knowledge"
        sources     = []

    return {
        "answer":      answer,
        "sources":     sources,
        "source_type": source_type,
    }


def _build_sources(docs) -> list[dict]:
    """Build deduplicated sources list from retrieved documents."""
    seen    = set()
    sources = []
    for doc in docs:
        key = (
            doc.metadata.get("source", ""),
            doc.metadata.get("slide_number", ""),
        )
        if key not in seen:
            seen.add(key)
            sources.append({
                "file":         doc.metadata.get("source", ""),
                "slide_number": doc.metadata.get("slide_number", ""),
                "subfolder":    doc.metadata.get("subfolder", ""),
                "lang_hint":    doc.metadata.get("lang_hint", ""),
            })
    return sources