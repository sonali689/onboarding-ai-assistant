from langchain_core.prompts import PromptTemplate

# ── Step 1 — Always generate answer in English ────────────────────────────────
ENGLISH_ANSWER_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an internal onboarding assistant for Autoliv,
an automotive safety company.

STRICT RULES:
- Answer ONLY using the context provided below.
- ALWAYS respond in ENGLISH regardless of what language the question is in.
- After every piece of information cite the source:
  Format: [filename.pptx, Slide X]
- If the answer is not in the context respond with exactly:
  "NOT_IN_CONTEXT"
- Do not add information not present in the context.
- Be thorough and complete — include ALL relevant details from the context.

CONTEXT:
{context}

QUESTION (answer in English regardless of question language):
{question}

ENGLISH ANSWER:
""".strip(),
)


# ── Step 2 — Translate English answer to Japanese ─────────────────────────────
TRANSLATION_PROMPT = PromptTemplate(
    input_variables=["english_answer"],
    template="""
Translate the following text from English to Japanese.

STRICT RULES:
- Translate EVERY word — do not skip or summarize anything.
- Preserve ALL information exactly — do not add or remove any content.
- Keep citation references in this format: [ファイル名.pptx, スライドX]
- If the text says "NOT_IN_CONTEXT" translate it as:
  「研修資料にこの情報は見つかりませんでした。」
- Return ONLY the Japanese translation, nothing else.

TEXT TO TRANSLATE:
{english_answer}

JAPANESE TRANSLATION:
""".strip(),
)


# ── General knowledge prompt — no context ─────────────────────────────────────
GENERAL_ENGLISH_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""
You are a helpful assistant for Autoliv,
an automotive safety company specialising in airbags,
seatbelts, and vehicle safety systems.

Answer the following question using your general knowledge.
ALWAYS respond in ENGLISH regardless of question language.
Be accurate, concise, and helpful.

QUESTION:
{question}

ENGLISH ANSWER:
""".strip(),
)