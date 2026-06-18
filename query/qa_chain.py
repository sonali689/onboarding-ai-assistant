import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama

from query.retriever import retrieve_chunks
from query.prompt_templates import (
    CONDENSE_QUESTION_PROMPT,
    TRANSLATE_QUESTION_TO_ENGLISH_PROMPT,
    GENERAL_ANSWER_PROMPT,
    AUTOLIV_CONTEXT_PROMPT,
    TRANSLATE_ANSWER_TO_JAPANESE_PROMPT,
)
from config import QWEN2_MODEL, OLLAMA_BASE_URL

_llm = None

MAX_HISTORY_MESSAGES   = 6     # last 3 exchanges
MAX_HISTORY_CHARS_EACH = 400   # trim long assistant answers


# ── LLM CONFIGURATION ─────────────────────────────────────────────────────────

def get_llm() -> ChatOllama:
    """
    Returns a unified ChatOllama instance with thinking mode disabled.
    Qwen3.5 generates internal reasoning tokens by default, which can
    consume the entire token budget on long structured prompts and
    leave no room for the actual answer. Disabling it fixes this.
    """
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=QWEN2_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            num_predict=1500,
            extra_body={"think": False},
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


# ── History formatting ─────────────────────────────────────────────────────────

def format_history(history: list[dict]) -> str:
    """
    Format recent conversation turns into plain text for the condense prompt.
    Expects history as list of {"role": "user"|"assistant", "content": str}.
    """
    if not history:
        return ""

    recent = history[-MAX_HISTORY_MESSAGES:]
    lines  = []
    for msg in recent:
        role    = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")[:MAX_HISTORY_CHARS_EACH]
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


# ── Translation / question resolution ──────────────────────────────────────────

def translate_to_english(text: str) -> str:
    print("[LLM RUN] Translating input question to English...")
    llm   = get_llm()
    chain = TRANSLATE_QUESTION_TO_ENGLISH_PROMPT | llm | StrOutputParser()
    return chain.invoke({"text": text}).strip()


def resolve_question(question: str, history: list[dict]) -> str:
    """
    Turn the latest message into a self-contained English question.
    Uses conversation history to resolve pronouns/follow-ups.
    Falls back to plain translation if there's no history.
    """
    lang = detect_language(question)

    if history:
        print("[LLM RUN] Condensing conversation history and question...")
        llm   = get_llm()
        chain = CONDENSE_QUESTION_PROMPT | llm | StrOutputParser()
        return chain.invoke({
            "history":  format_history(history),
            "question": question,
        }).strip()

    if lang == 'ja':
        return translate_to_english(question)

    return question


def translate_to_japanese(text: str) -> str:
    print("[LLM RUN] Translating full combined response to Japanese...")
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
    print("[LLM RUN] Generating general knowledge background...")
    llm   = get_llm()
    chain = GENERAL_ANSWER_PROMPT | llm | StrOutputParser()
    return chain.invoke({"question": question}).strip()


# ── Part 2 — Autoliv-specific context ──────────────────────────────────────────

def get_autoliv_context(question: str, docs) -> str | None:
    print("[LLM RUN] Analyzing vector database context chunks...")
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

def ask(question: str, history: list[dict] | None = None) -> dict:
    """
    Conversational two-part response pipeline.

    1. Resolve the latest message into a standalone English question.
    2. Generate a natural-language general explanation.
    3. Retrieve relevant chunks and write an Autoliv-specific context explanation.
    4. Combine both fields and process i18n localization transitions if necessary.
    """
    history = history or []

    # Step 1 — Detect language of the raw latest message
    lang = detect_language(question)

    # Step 2 — Resolve into standalone English question
    en_question = resolve_question(question, history)
    print(f"[RAG] lang={lang} | resolved question: {en_question}")

    # Step 3 — Part 1: General knowledge
    general_answer = get_general_answer(en_question)
    print(f"[RAG] General answer generation complete: {len(general_answer)} chars")

    # Step 4 — Retrieve from database
    try:
        print("[RAG] Querying vector database...")
        docs = retrieve_chunks(en_question)
        print(f"[RAG] Retrieved {len(docs)} chunks from storage.")
    except Exception as e:
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
            print(f"[RAG] Autoliv context parsing complete: {len(autoliv_context)} chars")
        else:
            print("[RAG] No explicit Autoliv-specific data matched the request context.")
    else:
        print("[RAG] Content criteria checks evaluated chunks as not relevant enough.")

    # Step 6 — Combine naturally
    if autoliv_context:
        combined_english = (
            f"{general_answer}\n\n"
            f"---\n\n"
            f"**At Autoliv**\n\n"
            f"{autoliv_context}"
        )
    else:
        combined_english = general_answer

    # Step 7 — Translate back if Japanese
    if lang == 'ja':
        print("[RAG] Input was Japanese. Initiating pipeline localization...")
        final_answer = translate_to_japanese(combined_english)
    else:
        final_answer = combined_english

    print("[RAG] Generation pipeline finalized completely.")
    return {
        "answer":      final_answer,
        "sources":      sources,
        "source_type": source_type,
    }