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
    RELEVANCE_FILTER_PROMPT,
    GENERAL_ANSWER_PROMPT,
    AUTOLIV_CONTEXT_PROMPT,
    TRANSLATE_ANSWER_TO_JAPANESE_PROMPT,
)
from config import (
    STANDARD_MODEL, EXTENDED_MODEL, OLLAMA_BASE_URL,
    TOP_K, TOP_K_EXTENDED,
)

_llms: dict[str, ChatOllama] = {}

MAX_HISTORY_MESSAGES    = 6
MAX_HISTORY_CHARS_EACH  = 400
RELEVANCE_PREVIEW_CHARS = 350


# ── LLM CONFIGURATION ─────────────────────────────────────────────────────────

def _build_llm(model: str, num_predict: int, temperature: float = 0.1) -> ChatOllama:
    return ChatOllama(
        model=model,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=num_predict,
    )


def get_llm(level: str = "standard") -> ChatOllama:
    key = level
    if key not in _llms:
        if level == "extended":
            _llms[key] = _build_llm(EXTENDED_MODEL, num_predict=2500, temperature=0.15)
        else:
            _llms[key] = _build_llm(STANDARD_MODEL, num_predict=1500, temperature=0.1)
    return _llms[key]


def get_extraction_llm(level: str = "standard") -> ChatOllama:
    key = f"{level}_extract"
    if key not in _llms:
        if level == "extended":
            _llms[key] = _build_llm(EXTENDED_MODEL, num_predict=2500, temperature=0.1)
        else:
            _llms[key] = _build_llm(STANDARD_MODEL, num_predict=1500, temperature=0.1)
    return _llms[key]


def get_filter_llm() -> ChatOllama:
    key = "filter"
    if key not in _llms:
        _llms[key] = _build_llm(STANDARD_MODEL, num_predict=60, temperature=0.0)
    return _llms[key]


def get_utility_llm() -> ChatOllama:
    return get_llm("standard")


def get_depth_instruction(level: str) -> str:
    if level == "extended":
        return (
            "DEPTH MODE: EXTENDED. Provide a thorough, in-depth analysis. "
            "Explore relevant trade-offs, edge cases, and technical nuance "
            "where it genuinely adds value. It is fine to write more if the "
            "topic calls for it."
        )
    return (
        "DEPTH MODE: STANDARD. Keep the explanation clear, accurate, and "
        "to the point — thorough but not padded."
    )


def invoke_with_retry(chain, inputs: dict, label: str) -> str:
    result = chain.invoke(inputs)
    result = result.strip() if isinstance(result, str) else str(result).strip()

    if not result:
        print(f"[RAG] WARNING: {label} returned empty content. Retrying once...")
        result = chain.invoke(inputs)
        result = result.strip() if isinstance(result, str) else str(result).strip()

    return result


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
    llm   = get_utility_llm()
    chain = TRANSLATE_QUESTION_TO_ENGLISH_PROMPT | llm | StrOutputParser()
    return invoke_with_retry(chain, {"text": text}, "translate_to_english")


def resolve_question(question: str, history: list[dict]) -> str:
    lang = detect_language(question)

    if history:
        print("[LLM RUN] Condensing conversation history and question...")
        llm   = get_utility_llm()
        chain = CONDENSE_QUESTION_PROMPT | llm | StrOutputParser()
        return invoke_with_retry(
            chain,
            {"history": format_history(history), "question": question},
            "resolve_question",
        )

    if lang == 'ja':
        return translate_to_english(question)

    return question


def translate_to_japanese(text: str) -> str:
    print("[LLM RUN] Translating full combined response to Japanese...")
    llm   = get_utility_llm()
    chain = TRANSLATE_ANSWER_TO_JAPANESE_PROMPT | llm | StrOutputParser()
    return invoke_with_retry(chain, {"text": text}, "translate_to_japanese")


# ── Relevance filtering ─────────────────────────────────────────────────────────

def filter_relevant_docs(question: str, docs: list) -> list:
    if not docs:
        return []

    numbered = []
    for i, doc in enumerate(docs, start=1):
        preview = doc.page_content[:RELEVANCE_PREVIEW_CHARS].replace("\n", " ")
        numbered.append(f"[{i}] {preview}")
    chunks_text = "\n\n".join(numbered)

    llm   = get_filter_llm()
    chain = RELEVANCE_FILTER_PROMPT | llm | StrOutputParser()
    result = invoke_with_retry(
        chain,
        {"question": question, "chunks": chunks_text},
        "filter_relevant_docs",
    )

    print(f"[RAG] Relevance filter result: {result!r}")

    if not result or "NONE" in result.upper():
        return []

    indices = []
    for part in result.replace(" ", "").split(","):
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(docs):
                indices.append(idx)

    seen, filtered = set(), []
    for idx in indices:
        if idx not in seen:
            seen.add(idx)
            filtered.append(docs[idx - 1])

    return filtered


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


def has_enough_text(docs) -> bool:
    if not docs:
        return False
    return len(" ".join(d.page_content for d in docs).strip()) >= 100


# ── Part 1 — General knowledge ─────────────────────────────────────────────────

def get_general_answer(question: str, level: str = "standard") -> str:
    print(f"[LLM RUN] Generating general knowledge background ({level})...")
    llm   = get_llm(level)
    chain = GENERAL_ANSWER_PROMPT | llm | StrOutputParser()
    result = invoke_with_retry(
        chain,
        {"question": question, "depth_instruction": get_depth_instruction(level)},
        "get_general_answer",
    )

    if not result and level == "extended":
        llm_fallback   = get_llm("standard")
        chain_fallback = GENERAL_ANSWER_PROMPT | llm_fallback | StrOutputParser()
        result = invoke_with_retry(
            chain_fallback,
            {"question": question, "depth_instruction": get_depth_instruction("standard")},
            "get_general_answer_fallback",
        )

    if not result:
        result = (
            "I wasn't able to generate a response right now. "
            "Please try rephrasing your question or try again in a moment."
        )

    return result


# ── Part 2 — Autoliv-specific context ──────────────────────────────────────────

def get_autoliv_context(question: str, docs, level: str = "standard") -> str | None:
    print(f"[LLM RUN] Writing Autoliv-specific explanation ({level})...")
    context = format_docs(docs)

    llm   = get_extraction_llm(level)
    chain = AUTOLIV_CONTEXT_PROMPT | llm | StrOutputParser()
    result = invoke_with_retry(
        chain,
        {
            "context":           context,
            "question":          question,
            "depth_instruction": get_depth_instruction(level),
        },
        "get_autoliv_context",
    )

    if not result and level == "extended":
        llm_fallback   = get_extraction_llm("standard")
        chain_fallback = AUTOLIV_CONTEXT_PROMPT | llm_fallback | StrOutputParser()
        result = invoke_with_retry(
            chain_fallback,
            {
                "context":           context,
                "question":          question,
                "depth_instruction": get_depth_instruction("standard"),
            },
            "get_autoliv_context_fallback",
        )

    if not result:
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


# ── Main pipeline (non-streaming, kept for fallback/testing) ──────────────────

def ask(
    question: str,
    history: list[dict] | None = None,
    level: str = "standard",
) -> dict:
    history = history or []
    if level not in ("standard", "extended"):
        level = "standard"

    lang = detect_language(question)
    en_question = resolve_question(question, history)
    print(f"[RAG] lang={lang} | level={level} | resolved question: {en_question}")

    general_answer = get_general_answer(en_question, level)
    retrieval_k = TOP_K_EXTENDED if level == "extended" else TOP_K

    try:
        raw_docs = retrieve_chunks(en_question, k=retrieval_k)
    except Exception as e:
        print(f"[RAG] RETRIEVAL ERROR: {e}")
        print(traceback.format_exc())
        raw_docs = []

    autoliv_context = None
    sources         = []
    source_type     = "general_knowledge"

    if has_enough_text(raw_docs):
        relevant_docs = filter_relevant_docs(en_question, raw_docs)
        if relevant_docs:
            autoliv_context = get_autoliv_context(en_question, relevant_docs, level)
            if autoliv_context:
                sources     = build_sources(relevant_docs)
                source_type = "company_data"

    if autoliv_context:
        combined_english = f"{general_answer}\n\n---\n\n**At Autoliv**\n\n{autoliv_context}"
    else:
        combined_english = general_answer

    final_answer = translate_to_japanese(combined_english) if lang == 'ja' else combined_english

    return {
        "answer":      final_answer,
        "sources":     sources,
        "source_type": source_type,
    }


# ── Streaming pipeline ─────────────────────────────────────────────────────────

def ask_stream(
    question: str,
    history: list[dict] | None = None,
    level: str = "standard",
):
    """
    Generator yielding incremental events for streaming to the client:
      {"type": "token", "text": "..."}
      {"type": "done", "sources": [...], "source_type": "..."}
      {"type": "error", "message": "..."}
    """
    history = history or []
    if level not in ("standard", "extended"):
        level = "standard"

    try:
        lang = detect_language(question)
        en_question = resolve_question(question, history)
        print(f"[RAG-STREAM] lang={lang} | level={level} | resolved question: {en_question}")

        retrieval_k = TOP_K_EXTENDED if level == "extended" else TOP_K
        try:
            raw_docs = retrieve_chunks(en_question, k=retrieval_k)
        except Exception as e:
            print(f"[RAG-STREAM] RETRIEVAL ERROR: {e}")
            raw_docs = []

        relevant_docs = []
        if has_enough_text(raw_docs):
            relevant_docs = filter_relevant_docs(en_question, raw_docs)
        print(f"[RAG-STREAM] {len(relevant_docs)}/{len(raw_docs)} chunks kept after relevance filter.")

        sources     = build_sources(relevant_docs) if relevant_docs else []
        source_type = "company_data" if relevant_docs else "general_knowledge"

        if lang == 'en':
            # ── Stream the general answer directly ──────────────────────
            llm   = get_llm(level)
            chain = GENERAL_ANSWER_PROMPT | llm | StrOutputParser()
            general_chunks = []
            for piece in chain.stream({
                "question": en_question,
                "depth_instruction": get_depth_instruction(level),
            }):
                if piece:
                    general_chunks.append(piece)
                    yield {"type": "token", "text": piece}

            if not "".join(general_chunks).strip():
                fallback = get_general_answer(en_question, "standard")
                yield {"type": "token", "text": fallback}

            # ── Stream the Autoliv section, if any ──────────────────────
            if relevant_docs:
                yield {"type": "token", "text": "\n\n---\n\n**At Autoliv**\n\n"}

                extraction_llm = get_extraction_llm(level)
                context_text   = format_docs(relevant_docs)
                chain2 = AUTOLIV_CONTEXT_PROMPT | extraction_llm | StrOutputParser()

                autoliv_chunks = []
                for piece in chain2.stream({
                    "context":           context_text,
                    "question":          en_question,
                    "depth_instruction": get_depth_instruction(level),
                }):
                    if piece:
                        autoliv_chunks.append(piece)
                        yield {"type": "token", "text": piece}

                autoliv_text = "".join(autoliv_chunks).strip()
                if not autoliv_text:
                    sources     = []
                    source_type = "general_knowledge"

        else:
            # ── Japanese — build full English text invisibly, stream translation ──
            general_answer = get_general_answer(en_question, level)

            autoliv_context = None
            if relevant_docs:
                autoliv_context = get_autoliv_context(en_question, relevant_docs, level)

            if autoliv_context:
                combined_english = f"{general_answer}\n\n---\n\n**At Autoliv**\n\n{autoliv_context}"
            else:
                combined_english = general_answer
                sources     = []
                source_type = "general_knowledge"

            llm   = get_utility_llm()
            chain = TRANSLATE_ANSWER_TO_JAPANESE_PROMPT | llm | StrOutputParser()
            ja_chunks = []
            for piece in chain.stream({"text": combined_english}):
                if piece:
                    ja_chunks.append(piece)
                    yield {"type": "token", "text": piece}

            if not "".join(ja_chunks).strip():
                yield {"type": "token", "text": combined_english}

        yield {"type": "done", "sources": sources, "source_type": source_type}

    except Exception as e:
        print(f"[RAG-STREAM] FATAL ERROR: {e}")
        print(traceback.format_exc())
        yield {"type": "error", "message": str(e)}