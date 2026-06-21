from langchain_core.prompts import PromptTemplate


# ── Condense follow-up question using conversation history ────────────────────
CONDENSE_QUESTION_PROMPT = PromptTemplate(
    input_variables=["history", "question"],
    template="""You are processing a conversation between an employee and
an assistant about Autoliv products and automotive safety topics.

Given the conversation so far and the employee's latest message, rewrite
the latest message as a fully self-contained question in English.

RULES:
- Replace pronouns like "it", "that", "this one" with the actual subject
  discussed earlier in the conversation.
- If the latest message is already a complete, self-contained question,
  just translate it to English if needed — otherwise return it as-is.
- Always output the result in English, regardless of what language the
  conversation was in.
- Return ONLY the rewritten standalone question, nothing else.

CONVERSATION SO FAR:
{history}

LATEST MESSAGE: {question}

STANDALONE ENGLISH QUESTION:""",
)


# ── Translate a question with no prior history ──────────────────────────────
TRANSLATE_QUESTION_TO_ENGLISH_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""Translate this Japanese text to English.
Return ONLY the English translation, nothing else.

Japanese: {text}
English:""",
)


# ── Relevance filtering — decide which retrieved chunks actually matter ───────
RELEVANCE_FILTER_PROMPT = PromptTemplate(
    input_variables=["question", "chunks"],
    template="""You are filtering search results for relevance.

Below are numbered excerpts from a company's internal training materials,
followed by a question. Decide which excerpts would help answer the
question.

An excerpt is relevant if:
- It discusses the same topic, product, process, or concept as the question
- It contains definitions, specifications, procedures, or facts related to the question
- It provides context that would help someone understand the answer

An excerpt is NOT relevant only if it is clearly about a completely
different subject with no connection to the question.

WHEN IN DOUBT, INCLUDE IT — it is better to include a borderline excerpt
than to miss useful information.

EXCERPTS:
{chunks}

QUESTION: {question}

Respond with ONLY a comma-separated list of the relevant excerpt numbers
(for example: 1,2,5,7). If none of the excerpts have ANY connection to
the question at all, respond with exactly: NONE
Do not explain. Output only the numbers or NONE.

RELEVANT EXCERPT NUMBERS:""",
)


# ── PRIMARY ANSWER: Document-grounded Autoliv-specific response ───────────────
AUTOLIV_ANSWER_PROMPT = PromptTemplate(
    input_variables=["context", "question", "depth_instruction"],
    template="""You are the Autoliv onboarding assistant. Your job is to
answer questions using ONLY the company training materials provided below.

Read the materials carefully and extract EVERY relevant detail — specific
names, numbers, model numbers, process steps, specifications, dates,
acronyms, and technical terms. Do not skip or summarize away details
that are present in the materials.

Write your answer as clear, natural prose — the way a senior colleague
would explain something in person. Use bullet points or short lists when
naming several distinct items, but otherwise write in flowing paragraphs.

ABSOLUTE RULES:
- Use ONLY information from the training materials below. Do not add
  outside knowledge, assumptions, or general industry information.
- If the materials contain a direct answer, give it confidently and
  completely. Extract every relevant fact.
- If the materials contain partial information, explain what IS covered
  and note what aspects aren't addressed in these specific materials.
- Never fabricate information that isn't in the materials.
- Never reference filenames, slide numbers, or "[Source: ...]" markers
  in your answer — the sources are shown separately to the reader.
- Do not open with a framing sentence about what you're about to explain.
  Start directly with the answer.
- Never write numbered Q&A headers like "1. What is..." or "2. How does..."
- Always respond in English.

{depth_instruction}

TRAINING MATERIALS:
{context}

QUESTION: {question}

Answer based on the training materials:""",
)


# ── FALLBACK: General knowledge when no documents match ───────────────────────
GENERAL_FALLBACK_PROMPT = PromptTemplate(
    input_variables=["question", "depth_instruction"],
    template="""You are the Autoliv onboarding assistant. The employee
asked a question, but no relevant information was found in the company's
training materials for this specific topic.

Provide a helpful general explanation based on common automotive safety
knowledge. Be clear that this is general information, not specific to
Autoliv's internal processes or products.

Write naturally and conversationally, as a knowledgeable colleague would.
Start directly with the explanation — no preamble about "since I couldn't
find..." or similar framing.

RULES:
- Keep it concise and genuinely helpful.
- Do not pretend this information comes from Autoliv's training materials.
- Always respond in English.
- Start directly with the subject matter.

{depth_instruction}

QUESTION: {question}

Explanation:""",
)


# ── Full answer translation — English to Japanese ──────────────────────────────
TRANSLATE_ANSWER_TO_JAPANESE_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""Translate the following English text to Japanese.

STRICT RULES:
- Translate EVERYTHING completely — do not skip or summarize anything
- Preserve the natural, conversational tone — do not make it sound
  more formal or robotic than the English version
- Preserve markdown formatting (**, ---, etc.)
- Return ONLY the Japanese translation, nothing else

English:
{text}

Japanese:""",
)