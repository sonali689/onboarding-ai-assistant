import unicodedata
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
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

    IMPORTANT: Every chunk gets a context prefix with the slide title
    and source file, so even after splitting, each chunk is
    self-describing and can be matched to queries independently.
    """
    # ── Build the context prefix that goes on EVERY chunk ─────────────
    context_prefix = (
        f"[CONTEXT: {slide_data['slide_title']} | "
        f"Source: {slide_data['filename']} | "
        f"Category: {slide_data['subfolder']}]\n\n"
    )

    # ── Build the content to be split ─────────────────────────────────
    parts = []

    if slide_data['text'].strip():
        parts.append(slide_data['text'].strip())

    if slide_data['notes'].strip():
        parts.append(f"Speaker Notes: {slide_data['notes'].strip()}")

    if vision_description.strip():
        parts.append(f"Visual Description: {vision_description.strip()}")

    combined_content = "\n\n".join(parts)

    if not combined_content.strip():
        return []

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
            ". ",     # English sentence boundary
            " ",      # spaces (English)
            "",       # character-level fallback (last resort)
        ],
    )

    raw_chunks = splitter.create_documents(
        texts=[combined_content],
        metadatas=[metadata],
    )

    # ── Prepend context prefix to EVERY chunk ─────────────────────────
    # This ensures that even when content splits across chunks,
    # each chunk carries its slide title and source for better
    # embedding matching and LLM comprehension.
    for chunk in raw_chunks:
        chunk.page_content = context_prefix + chunk.page_content

    return raw_chunks