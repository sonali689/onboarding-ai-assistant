import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms      import Ollama

from query.retriever import retrieve_chunks
from query.prompt_templates import (
    GENERAL_ANSWER_PROMPT,
    AUTOLIV_CONTEXT_PROMPT,
    TRANSLATE_QUESTION_TO_ENGLISH_PROMPT,
    TRANSLATE_ANSWER_TO_JAPANESE_PROMPT,
)
from config import QWEN2_MODEL, OLLAMA_BASE_URL

_llm = None


# ── LLM ───────────────────────────────────────────────────────────────────────

def get_llm() -> Ollama:
    global _llm
    if _llm is None:
        _llm = Ollama(
            model=QWEN2_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            num_predict=1500,
        )
    return _llm


# ── Language detection ─────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    for c in text:
        if (
            '\u3040' <= c <= '\u309f'
            or '\u30a0' <= c <= '\u30ff'
            or '\u4e00' <= c <= '\u9fff'
        ):
            return 'ja'
    return 'en'


# ── Translation ────────────────────────────────────────────────────────────────

def translate_to_english(text: str) -> str:
    """Translate Japanese question to English for processing."""
    llm   = get_llm()
    chain = TRANSLATE_QUESTION_TO_ENGLISH_PROMPT | llm | StrOutputParser()
    return chain.invoke({"text": text}).strip()


def translate_to_japanese(text: str) -> str:
    """
    Translate full English response to Japanese.
    Preserves tone, formatting, and citations exactly.
    """
    llm   = get_llm()
    chain = TRANSLATE_ANSWER_TO_JAPANESE_PROMPT | llm | StrOutputParser()
    return chain.invoke({"text": text}).strip()


# ── Context formatting ─────────────────────────────────────────────────────────

def format_docs(docs) -> str:
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


def is_relevant(docs) -> bool:
    if not docs:
        return False
    return len(" ".join(d.page_content for d in docs).strip()) >= 100


# ── Part 1 — General knowledge ─────────────────────────────────────────────────

def get_general_answer(question: str) -> str:
    """
    Natural-language answer from LLM training knowledge.
    No database involved. Always high quality and language-independent.
    """
    llm   = get_llm()
    chain = GENERAL_ANSWER_PROMPT | llm | StrOutputParser()
    return chain.invoke({"question": question}).strip()


# ── Part 2 — Autoliv-specific context ──────────────────────────────────────────

def get_autoliv_context(question: str, docs) -> str | None:
    """
    Write a natural explanation of what Autoliv's training materials
    say about the topic. Returns None if nothing meaningful found.
    """
    llm     = get_llm()
    context = format_docs(docs)
    chain   = AUTOLIV_CONTEXT_PROMPT | llm | StrOutputParser()

    result = chain.invoke({
        "context":  context,
        "question": question,
    }).strip()

    if "NO_AUTOLIV_CONTEXT" in result:
        return None
    return result


# ── Sources ────────────────────────────────────────────────────────────────────

def build_sources(docs) -> list[dict]:
    seen, sources = set(), []
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


# ── Main pipeline ──────────────────────────────────────────────────────────────

def ask(question: str) -> dict:
    """
    Two-part response pipeline:

    Part 1 — General knowledge answer from LLM training data.
              Always high quality. Never depends on database.
              Written as natural prose explaining what it is,
              how it works, and why it matters.

    Part 2 — Autoliv-specific context from ChromaDB.
              Written as a natural explanation of how Autoliv
              specifically approaches the topic, with citations
              woven into the sentences. Only shown when the
              database has genuinely relevant content.

    Both parts generated in English first.
    Full response translated at the end if question was Japanese.
    """
    # Step 1 — Detect language
    lang = detect_language(question)

    # Step 2 — Translate to English for all processing
    if lang == 'ja':
        en_question = translate_to_english(question)
    else:
        en_question = question

    print(f"[RAG] lang={lang} | EN question: {en_question}")

    # Step 3 — Part 1: General knowledge (no database)
    general_answer = get_general_answer(en_question)
    print(f"[RAG] General answer: {len(general_answer)} chars")

    # Step 4 — Retrieve from database using English question
    try:
        docs = retrieve_chunks(en_question)
        print(f"[RAG] Retrieved {len(docs)} chunks")
    except Exception as e:
        import traceback
        print(f"[RAG] RETRIEVAL ERROR: {e}")
        print(traceback.format_exc())
        docs = []

    # Step 5 — Part 2: Autoliv-specific context
    autoliv_context = None
    sources         = []
    source_type     = "general_knowledge"

    if is_relevant(docs):
        autoliv_context = get_autoliv_context(en_question, docs)
        if autoliv_context:
            sources     = build_sources(docs)
            source_type = "company_data"
            print(f"[RAG] Autoliv context: {len(autoliv_context)} chars")
        else:
            print("[RAG] No Autoliv-specific context found")
    else:
        print("[RAG] Chunks not relevant enough")

    # Step 6 — Combine both parts naturally
    if autoliv_context:
        combined_english = (
            f"{general_answer}\n\n"
            f"---\n\n"
            f"**At Autoliv**\n\n"
            f"{autoliv_context}"
        )
    else:
        combined_english = general_answer

    # Step 7 — Translate whole response if Japanese
    if lang == 'ja':
        print("[RAG] Translating full response to Japanese")
        final_answer = translate_to_japanese(combined_english)
    else:
        final_answer = combined_english

    return {
        "answer":      final_answer,
        "sources":     sources,
        "source_type": source_type,
    }