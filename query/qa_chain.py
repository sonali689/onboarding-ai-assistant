import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama

from query.prompt_templates import BILINGUAL_PROMPT
from query.retriever import get_retriever, retrieve_chunks
from config import QWEN2_MODEL, OLLAMA_BASE_URL

# Cached instances — built once, reused for every question
_llm      = None
_chain    = None
_retriever = None


def get_llm() -> Ollama:
    """Return cached Ollama LLM instance."""
    global _llm
    if _llm is None:
        _llm = Ollama(
            model=QWEN2_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
    return _llm


def format_docs(docs) -> str:
    """
    Format retrieved documents into a single context string.
    Preserves all Japanese and English content exactly.
    """
    parts = []
    for doc in docs:
        source     = doc.metadata.get("source", "")
        slide_num  = doc.metadata.get("slide_number", "")
        subfolder  = doc.metadata.get("subfolder", "")
        parts.append(
            f"[Source: {source} | Slide {slide_num} | {subfolder}]\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)


def build_chain():
    """
    Build and return the full RAG chain using LCEL.
    Modern replacement for the deprecated RetrievalQA.
    """
    global _chain, _retriever
    if _chain is not None:
        return _chain, _retriever

    llm       = get_llm()
    retriever = get_retriever()

    _chain = (
        {
            "context":  retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | BILINGUAL_PROMPT
        | llm
        | StrOutputParser()
    )
    _retriever = retriever
    return _chain, _retriever


def ask(question: str) -> dict:
    """
    Run a question through the full RAG pipeline.

    Returns:
        {
            "answer":  str,
            "sources": list of dicts with file, slide_number,
                       subfolder, lang_hint
        }
    """
    chain, retriever = build_chain()

    # Retrieve source docs separately so we can return them
    source_docs = retrieve_chunks(question)

    # Run the chain to get the answer
    answer = chain.invoke(question)

    # Build deduplicated sources list
    seen    = set()
    sources = []
    for doc in source_docs:
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

    return {
        "answer":  answer,
        "sources": sources,
    }