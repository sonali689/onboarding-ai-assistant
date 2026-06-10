import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from query.prompt_templates import BILINGUAL_PROMPT
from query.retriever import get_retriever
from config import QWEN2_MODEL, OLLAMA_BASE_URL

# Cached instance — built once, reused for every question in the session
_qa_chain = None


def build_qa_chain() -> RetrievalQA:
    """
    Build and return the full RAG chain.
    Cached after first call so model is not reloaded on every question.
    """
    global _qa_chain
    if _qa_chain is not None:
        return _qa_chain

    llm = Ollama(
        model=QWEN2_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    retriever = get_retriever()

    _qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": BILINGUAL_PROMPT},
    )
    return _qa_chain


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
    chain = build_qa_chain()
    result = chain.invoke({"query": question})

    sources = []
    for doc in result.get("source_documents", []):
        sources.append({
            "file":         doc.metadata.get("source", ""),
            "slide_number": doc.metadata.get("slide_number", ""),
            "subfolder":    doc.metadata.get("subfolder", ""),
            "lang_hint":    doc.metadata.get("lang_hint", ""),
        })

    # Deduplicate sources — same slide can appear in multiple chunks
    seen = set()
    unique_sources = []
    for s in sources:
        key = (s["file"], s["slide_number"])
        if key not in seen:
            seen.add(key)
            unique_sources.append(s)

    return {
        "answer":  result["result"],
        "sources": unique_sources,
    }