import base64
import ollama
from config import LLAVA_MODEL, OLLAMA_BASE_URL

BILINGUAL_VISION_PROMPT = """
This training slide may contain English text, Japanese text, or a mixture of both.

Please do ALL of the following:
1. Describe every diagram, chart, flowchart, table, or visual element in detail.
2. Transcribe all visible text exactly as it appears:
   - Preserve all Japanese characters (hiragana, katakana, kanji) exactly
   - Preserve all English text exactly
3. Explain what the slide is communicating overall.

DO NOT translate anything.
Preserve all original text in its original language.
"""


def describe_slide_image(image_path: str) -> str:
    """
    Send a slide image to LLaVA via Ollama and get a bilingual description.
    Returns empty string if LLaVA fails — does not crash the pipeline.
    """
    try:
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")

        response = ollama.chat(
            model=LLAVA_MODEL,
            messages=[{
                "role":    "user",
                "content": BILINGUAL_VISION_PROMPT,
                "images":  [img_data],
            }],
            options={"base_url": OLLAMA_BASE_URL},
        )
        return response["message"]["content"]

    except Exception as e:
        print(f"  ⚠️  LLaVA failed on {image_path}: {e}")
        return ""