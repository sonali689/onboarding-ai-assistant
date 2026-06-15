import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts        import PromptTemplate
from langchain_community.llms      import Ollama

from query.retriever import retrieve_chunks
from config          import QWEN2_MODEL, OLLAMA_BASE_URL

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
    chain = PromptTemplate(
        input_variables=["text"],
        template=(
            "Translate this Japanese text to English.\n"
            "Return ONLY the English translation, nothing else.\n\n"
            "Japanese: {text}\n"
            "English:"
        ),
    ) | llm | StrOutputParser()
    return chain.invoke({"text": text}).strip()


def translate_to_japanese(text: str) -> str:
    """
    Translate full English response to Japanese.
    Preserves all markdown formatting and citations exactly.
    """
    llm   = get_llm()
    chain = PromptTemplate(
        input_variables=["text"],
        template=(
            "Translate the following English text to Japanese.\n\n"
            "STRICT RULES:\n"
            "- Translate EVERYTHING completely — do not skip or summarize\n"
            "- Preserve ALL markdown formatting (**, ##, ---, etc.)\n"
            "- Keep citations as: [ファイル名.pptx, スライドX]\n"
            "- Return ONLY the Japanese translation, nothing else\n\n"
            "English:\n{text}\n\n"
            "Japanese:"
        ),
    ) | llm | StrOutputParser()
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
    Answer from LLM training knowledge — no database involved.
    Always high quality and language-independent.
    """
    llm   = get_llm()
    chain = PromptTemplate(
        input_variables=["question"],
        template="""You are a knowledgeable assistant specialising in
automotive safety systems including airbags, seatbelts, inflators,
sensors, propellants, crash testing, and vehicle safety engineering.

Answer the following question clearly and thoroughly using your knowledge.
Always respond in ENGLISH.

Give a complete explanation that helps someone new to the automotive
safety industry understand the topic well. Include:
- What it is and how it works
- Key types or categories if applicable
- Why it matters in automotive safety
- Any important technical details relevant to the industry

Use clear headings and bullet points where appropriate.

QUESTION: {question}

GENERAL ANSWER:""",
    ) | llm | StrOutputParser()
    return chain.invoke({"question": question}).strip()


# ── Part 2 — Autoliv-specific context ─────────────────────────────────────────

def get_autoliv_context(question: str, docs) -> str | None:
    """
    Extract ALL Autoliv-specific information from retrieved chunks.
    Returns None if nothing meaningful found in the database.
    """
    llm     = get_llm()
    context = format_docs(docs)

    chain = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are reading Autoliv's internal training materials.

Based on these training materials, extract and explain ALL of the
following about the topic in the question:

1. What types or variants does Autoliv use?
2. How does Autoliv use or implement this in their products/processes?
3. What specific products, models, or specifications does Autoliv have?
4. What is Autoliv's testing or validation approach for this?
5. Which Autoliv departments or teams work on this?
6. What standards or regulations does Autoliv follow for this?
7. Any other Autoliv-specific details mentioned in the materials?

RULES:
- Only include information actually present in the training materials
- Always respond in ENGLISH
- Cite every single piece of information: [filename.pptx, Slide X]
- Be thorough — extract EVERYTHING relevant from the materials
- Do not repeat general explanations — only Autoliv-specific details
- Use clear structure with bullet points and headings
- If the materials contain absolutely nothing about this topic,
  respond with exactly: NO_AUTOLIV_CONTEXT

TRAINING MATERIALS:
{context}

TOPIC: {question}

AUTOLIV-SPECIFIC DETAILS (cite everything):""",
    ) | llm | StrOutputParser()

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
              Explains what it is, how it works, types, etc.

    Part 2 — Autoliv-specific context from ChromaDB.
              What types Autoliv uses, how Autoliv implements it,
              products, specs, processes, teams, standards.
              Only shown when database has relevant content.

    Both parts generated in English first.
    Full response translated at the end if question was Japanese.

    This approach solves:
    - Language inconsistency (always generate EN, translate once at end)
    - Poor answers (general knowledge is always good)
    - Missing company context (database adds Autoliv-specific details)
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
    docs = retrieve_chunks(en_question)
    print(f"[RAG] Retrieved {len(docs)} chunks")

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

    # Step 6 — Combine both parts
    if autoliv_context:
        combined_english = (
            f"## General Overview\n\n"
            f"{general_answer}\n\n"
            f"---\n\n"
            f"## At Autoliv\n\n"
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