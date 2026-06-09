import unicodedata
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core import Document
from config import CHUNK_SIZE, CHUNK_OVERLAP


def detect_language_hint(text: str) -> str:
    """
    Returns 'ja', 'en', or 'mixed' based on character analysis.
    Used as metadata for debugging — does not affect retrieval.
    """
    has_cjk = any(
        ("\u4e00" <= c <= "\u9fff")  # CJK unified ideographs (kanji)
        or ("\u3040" <= c <= "\u309f")  # hiragana
        or ("\u30a0" <= c <= "\u30ff")  # katakana
        for c in text
    )
    has_latin = any(c.isalpha() and ord(c) < 128 for c in text)

    if has_cjk and has_latin:
        return "mixed"
    elif has_cjk:
        return "ja"
    return "en"


def chunk_slide_document(
    slide_data: dict,
    vision_description: str,
) -> list[Document]:
    """
    Combine slide text + vision description into chunks.
    Uses Japanese-aware splitter with punctuation separators.
    Returns list of LangChain Document objects with metadata.
    """
    combined_content = f"""
=== SLIDE {slide_data['slide_number']}: {slide_data['slide_title']} ===
SOURCE: {slide_data['filename']} | CATEGORY: {slide_data['subfolder']}

[Extracted Text]
{slide_data['text']}

[Speaker Notes]
{slide_data['notes']}

[Visual Description]
{vision_description}
""".strip()

    lang_hint = detect_language_hint(
        slide_data["text"] + vision_description
    )

    metadata = {
        "source":       slide_data["filename"],
        "slide_number": slide_data["slide_number"],
        "slide_title":  slide_data["slide_title"],
        "subfolder":    slide_data["subfolder"],
        "lang_hint":    lang_hint,
    }

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",   # paragraph breaks (highest priority)
            "。",     # Japanese full stop
            "．",     # full-width period
            "！",     # full-width exclamation
            "？",     # full-width question mark
            "、",     # Japanese comma
            "\n",     # line breaks
            " ",      # spaces (English)
            "",       # character-level fallback (last resort)
        ],
    )

    chunks = splitter.create_documents(
        texts=[combined_content],
        metadatas=[metadata],
    )
    return chunks