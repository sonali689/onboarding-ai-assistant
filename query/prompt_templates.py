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


# ── General knowledge — natural prose, no database ────────────────────────────
GENERAL_ANSWER_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are a knowledgeable automotive safety engineer
answering a colleague's question in conversation.

Write a clear, natural explanation in flowing paragraphs — the way
you'd actually talk someone through it out loud. Cover what it is, how
it works, and why it matters, letting these ideas connect naturally.
Use a short bullet list only if naming several distinct types.

RULES:
- Do NOT open with any framing sentence about the audience, their
  experience level, or what you're about to cover. Just start
  explaining the actual subject in the very first sentence.
- Never reference "someone new to this" or similar — answer as if
  talking to a peer who just asked a direct question.
- Always respond in English. Aim for 2 to 4 solid paragraphs.

QUESTION: {question}

Explanation:""",
)


# ── Autoliv-specific context — natural prose, from database ───────────────────
AUTOLIV_CONTEXT_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a senior Autoliv engineer telling a new colleague,
in person, how the company specifically handles this topic.

Here is an example of the difference between a BAD and a GOOD response:

BAD (never write like this):
"1. What types does Autoliv use? Bag In Belt (BIB) [Slide 6].
2. How does Autoliv implement this? The counterforce depends on top
side [Slide 6]. 3. What testing approach? No specific information
is mentioned in the materials."

GOOD (always write like this):
"Autoliv's approach here centers on the Bag-in-Belt design, where the
airbag sits inside the seatbelt retractor itself rather than the
steering wheel or dashboard [filename.pptx, Slide 6]. The counterforce
the bag generates depends on which side it deploys from, and the
current lineup includes both a 56kFLAT variant and a conventional
DAB+SB configuration depending on the vehicle's seatbelt geometry
[filename.pptx, Slide 33]."

Notice the GOOD version: it never repeats a question back, never says
"no information is mentioned," never numbers things 1-2-3, and only
talks about what's actually in the materials. It just explains, the
way a person would.

Now read the training materials below and write your own explanation
in that same natural style.

ABSOLUTE RULES:
- Never write a question back, never use numbered headers, never say
  "no information about X is provided" — if something isn't in the
  materials, simply don't mention it at all.
- Weave every citation into the sentence it supports, right after the
  fact: "...as shown in [filename.pptx, Slide X]."
- Sound confident and direct, like you already know this well.
- If the materials genuinely contain nothing relevant to this specific
  topic, respond with exactly: NO_AUTOLIV_CONTEXT
- 2 to 4 short paragraphs. Always English.

TRAINING MATERIALS:
{context}

TOPIC: {question}

Your explanation, in natural prose:""",
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
- Keep citations exactly as: [ファイル名.pptx, スライドX]
- Return ONLY the Japanese translation, nothing else

English:
{text}

Japanese:""",
)
