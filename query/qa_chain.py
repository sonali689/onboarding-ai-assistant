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
    GENERAL_FALLBACK_PROMPT,
    AUTOLIV_ANSWER_PROMPT,
    ENGLISH_CLEANUP_PROMPT,
    TRANSLATE_ANSWER_TO_JAPANESE_PROMPT,
)
from config import (
    STANDARD_MODEL, EXTENDED_MODEL, OLLAMA_BASE_URL,
    TOP_K, TOP_K_EXTENDED, RELEVANCE_PREVIEW_CHARS,
)

_llms: dict[str, ChatOllama] = {}

MAX_HISTORY_MESSAGES    = 6
MAX_HISTORY_CHARS_EACH  = 400


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
        _llms[key] = _build_llm(STANDARD_MODEL, num_predict=100, temperature=0.0)
    return _llms[key]


def get_utility_llm() -> ChatOllama:
    return get_llm("standard")


def get_depth_instruction(level: str) -> str:
    if level == "extended":
        return (
            "DEPTH MODE: EXTENDED. Extract and present ALL details from the "
            "provided materials — every specification, every step, every "
            "variant mentioned. Organize the information thoroughly. Go "
            "deeper into the materials, not broader beyond them."
        )
    return (
        "DEPTH MODE: STANDARD. Give a clear, accurate, and complete "
        "answer covering the key points from the materials."
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


def is_mostly_japanese(text: str, threshold: float = 0.15) -> bool:
    """
    Checks whether text that was supposed to be pure English actually
    leaked a meaningful amount of Japanese. Used as a safety net before
    translating — translating already-Japanese-contaminated text
    produces garbled double-translation artifacts (e.g. "airbag"
    becoming "airsac").
    """
    if not text:
        return False
    cjk_count = sum(
        1 for c in text
        if ('\u3040' <= c <= '\u30ff') or ('\u4e00' <= c <= '\u9fff')
    )
    return (cjk_count / max(len(text), 1)) > threshold


def clean_up_english(text: str, level: str = "standard") -> str:
    """Rewrites contaminated text to be purely English, preserving facts."""
    print("[RAG] WARNING: English-stage answer leaked Japanese — cleaning up...")
    llm   = get_extraction_llm(level)
    chain = ENGLISH_CLEANUP_PROMPT | llm | StrOutputParser()
    result = invoke_with_retry(chain, {"text": text}, "clean_up_english")
    return result if result else text


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


# ── Autoliv document-grounded answer ───────────────────────────────────────────

def get_autoliv_answer(question: str, docs, level: str = "standard") -> str | None:
    """Generate answer grounded ONLY in retrieved training materials."""
    print(f"[LLM RUN] Writing document-grounded Autoliv answer ({level})...")
    context = format_docs(docs)

    llm   = get_extraction_llm(level)
    chain = AUTOLIV_ANSWER_PROMPT | llm | StrOutputParser()
    result = invoke_with_retry(
        chain,
        {
            "context":           context,
            "question":          question,
            "depth_instruction": get_depth_instruction(level),
        },
        "get_autoliv_answer",
    )

    if not result and level == "extended":
        llm_fallback   = get_extraction_llm("standard")
        chain_fallback = AUTOLIV_ANSWER_PROMPT | llm_fallback | StrOutputParser()
        result = invoke_with_retry(
            chain_fallback,
            {
                "context":           context,
                "question":          question,
                "depth_instruction": get_depth_instruction("standard"),
            },
            "get_autoliv_answer_fallback",
        )

    if result and is_mostly_japanese(result):
        result = clean_up_english(result, level)
    
    return result if result else None


# ── General knowledge fallback ─────────────────────────────────────────────────

def get_general_fallback(question: str, level: str = "standard") -> str:
    """Fallback answer when NO relevant documents are found."""
    print(f"[LLM RUN] No documents matched — generating general fallback ({level})...")
    llm   = get_llm(level)
    chain = GENERAL_FALLBACK_PROMPT | llm | StrOutputParser()
    result = invoke_with_retry(
        chain,
        {"question": question, "depth_instruction": get_depth_instruction(level)},
        "get_general_fallback",
    )

    if not result and level == "extended":
        llm_fallback   = get_llm("standard")
        chain_fallback = GENERAL_FALLBACK_PROMPT | llm_fallback | StrOutputParser()
        result = invoke_with_retry(
            chain_fallback,
            {"question": question, "depth_instruction": get_depth_instruction("standard")},
            "get_general_fallback_fallback",
        )

    if not result:
        result = (
            "I wasn't able to generate a response right now. "
            "Please try rephrasing your question or try again in a moment."
        )

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
    """
    Option B flow: Documents first. General knowledge ONLY as fallback.

    1. Resolve question (handle history, translate if Japanese)
    2. Retrieve chunks from ChromaDB
    3. Filter for relevance
    4. If relevant docs found → answer ONLY from documents
    5. If NO relevant docs → provide general knowledge fallback
    """
    history = history or []
    if level not in ("standard", "extended"):
        level = "standard"

    lang = detect_language(question)
    en_question = resolve_question(question, history)
    print(f"[RAG] lang={lang} | level={level} | resolved question: {en_question}")

    retrieval_k = TOP_K_EXTENDED if level == "extended" else TOP_K

    try:
        raw_docs = retrieve_chunks(en_question, k=retrieval_k)
    except Exception as e:
        print(f"[RAG] RETRIEVAL ERROR: {e}")
        print(traceback.format_exc())
        raw_docs = []

    # ── Try document-grounded answer first ─────────────────────────────
    answer      = None
    sources     = []
    source_type = "general_knowledge"

    if has_enough_text(raw_docs):
        relevant_docs = filter_relevant_docs(en_question, raw_docs)
        if relevant_docs:
            answer = get_autoliv_answer(en_question, relevant_docs, level)
            if answer:
                sources     = build_sources(relevant_docs)
                source_type = "company_data"

    # ── Fallback to general knowledge only if docs failed ──────────────
    if not answer:
        answer = get_general_fallback(en_question, level)

    # ── Translate if Japanese input ────────────────────────────────────
    #final_answer = translate_to_japanese(answer) if lang == 'ja' else answer

    if lang == 'ja':
        if is_mostly_japanese(answer):
            answer = clean_up_english(answer, level)
        final_answer = translate_to_japanese(answer)
    else:
        final_answer = answer

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

    Option B flow: Documents first. General knowledge ONLY as fallback.
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

        # ── Decide which prompt to use ─────────────────────────────────
        if relevant_docs:
            # DOCUMENT-GROUNDED answer
            llm          = get_extraction_llm(level)
            context_text = format_docs(relevant_docs)
            prompt       = AUTOLIV_ANSWER_PROMPT
            inputs       = {
                "context":           context_text,
                "question":          en_question,
                "depth_instruction": get_depth_instruction(level),
            }
        else:
            # GENERAL FALLBACK — no matching docs
            llm    = get_llm(level)
            prompt = GENERAL_FALLBACK_PROMPT
            inputs = {
                "question":          en_question,
                "depth_instruction": get_depth_instruction(level),
            }

        chain = prompt | llm | StrOutputParser()

        if lang == 'en':
            # ── Stream directly ────────────────────────────────────────
            answer_chunks = []
            for piece in chain.stream(inputs):
                if piece:
                    answer_chunks.append(piece)
                    yield {"type": "token", "text": piece}

            if not "".join(answer_chunks).strip():
                # Retry without streaming
                if relevant_docs:
                    fallback = get_autoliv_answer(en_question, relevant_docs, "standard")
                else:
                    fallback = get_general_fallback(en_question, "standard")
                if fallback:
                    yield {"type": "token", "text": fallback}

        else:
            # ── Japanese — build English invisibly, stream translation ──
            english_answer = invoke_with_retry(chain, inputs, "stream_build_english")

            if english_answer and is_mostly_japanese(english_answer):
                english_answer = clean_up_english(english_answer, level)

            if not english_answer:
                if relevant_docs:
                    english_answer = get_autoliv_answer(en_question, relevant_docs, "standard") or ""
                else:
                    english_answer = get_general_fallback(en_question, "standard")

            if not english_answer:
                sources     = []
                source_type = "general_knowledge"
                english_answer = (
                    "I wasn't able to generate a response right now. "
                    "Please try rephrasing your question or try again."
                )

            ja_llm  = get_utility_llm()
            ja_chain = TRANSLATE_ANSWER_TO_JAPANESE_PROMPT | ja_llm | StrOutputParser()
            ja_chunks = []
            for piece in ja_chain.stream({"text": english_answer}):
                if piece:
                    ja_chunks.append(piece)
                    yield {"type": "token", "text": piece}

            if not "".join(ja_chunks).strip():
                yield {"type": "token", "text": english_answer}

        yield {"type": "done", "sources": sources, "source_type": source_type}

    except Exception as e:
        print(f"[RAG-STREAM] FATAL ERROR: {e}")
        print(traceback.format_exc())
        yield {"type": "error", "message": str(e)}