"""
Staged ingestion test — run this before full ingestion.
Tests each step independently so failures are easy to isolate.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PPTX_FOLDER, SLIDE_IMAGE_FOLDER


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — Find PPTX files
# ─────────────────────────────────────────────────────────────────────────────
def test_stage1():
    print_header("STAGE 1 — Scan PPTX Files")
    from ingestion.pptx_extractor import scan_pptx_files

    files = scan_pptx_files()

    if not files:
        print("❌ No PPTX files found.")
        print(f"   Check that your files are inside: {PPTX_FOLDER}")
        return None

    print(f"✅ Found {len(files)} PPTX files\n")
    for f in files[:5]:   # show first 5 only
        print(f"   {f}")
    if len(files) > 5:
        print(f"   ... and {len(files) - 5} more")

    return files


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — Extract text from first PPTX
# ─────────────────────────────────────────────────────────────────────────────
def test_stage2(pptx_files: list):
    print_header("STAGE 2 — Text Extraction (first PPTX only)")
    from ingestion.pptx_extractor import extract_slide_data

    test_file = pptx_files[0]
    print(f"Testing on: {os.path.basename(test_file)}\n")

    slides = extract_slide_data(test_file)

    if not slides:
        print("❌ No slides extracted.")
        return None

    print(f"✅ Extracted {len(slides)} slides\n")

    # Show first 3 slides
    for slide in slides[:3]:
        print(f"  Slide {slide['slide_number']}: {slide['slide_title']}")
        print(f"  Lang preview: {slide['text'][:100].strip()}")
        print(f"  Notes: {'Yes' if slide['notes'] else 'None'}")
        print()

    return slides


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — Export slide images (first PPTX, first 3 slides only)
# ─────────────────────────────────────────────────────────────────────────────
def test_stage3(pptx_files: list):
    print_header("STAGE 3 — Slide Image Export (first PPTX only)")
    from ingestion.slide_exporter import export_slides_as_images

    test_file = pptx_files[0]
    print(f"Testing on: {os.path.basename(test_file)}\n")

    slide_images = export_slides_as_images(test_file)

    if not slide_images:
        print("❌ No images exported.")
        return None

    print(f"✅ Exported {len(slide_images)} images")
    for num, path in slide_images[:3]:
        exists = os.path.exists(path)
        size   = os.path.getsize(path) if exists else 0
        status = "✅" if exists and size > 1000 else "⚠️  (may be blank placeholder)"
        print(f"  Slide {num}: {os.path.basename(path)} "
              f"({size} bytes) {status}")

    return slide_images


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 4 — LLaVA vision description (first slide only)
# ─────────────────────────────────────────────────────────────────────────────
def test_stage4(slide_images: list):
    print_header("STAGE 4 — LLaVA Vision Description (first slide only)")
    from ingestion.vision_describer import describe_slide_image

    if not slide_images:
        print("⏭️  Skipping — no images from Stage 3.")
        return None

    first_slide_num, first_image_path = slide_images[0]
    print(f"Testing on: {os.path.basename(first_image_path)}\n")
    print("Sending to LLaVA... (may take 30–60 seconds)\n")

    description = describe_slide_image(first_image_path)

    if not description:
        print("❌ LLaVA returned empty description.")
        print("   Check Ollama is running: ollama serve")
        print("   Check LLaVA is pulled:   ollama list")
        return None

    print(f"✅ LLaVA description received ({len(description)} chars)\n")
    print("Preview:")
    print(description[:400])
    print("...")

    return description


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 5 — Chunking (first slide)
# ─────────────────────────────────────────────────────────────────────────────
def test_stage5(slides: list, vision_description: str):
    print_header("STAGE 5 — Chunking (first slide only)")
    from ingestion.chunker import chunk_slide_document

    if not slides:
        print("⏭️  Skipping — no slides from Stage 2.")
        return None

    vision_desc = vision_description or ""
    chunks = chunk_slide_document(slides[0], vision_desc)

    if not chunks:
        print("❌ No chunks produced.")
        return None

    print(f"✅ Produced {len(chunks)} chunks from slide 1\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}:")
        print(f"    lang_hint:    {chunk.metadata['lang_hint']}")
        print(f"    source:       {chunk.metadata['source']}")
        print(f"    slide_number: {chunk.metadata['slide_number']}")
        print(f"    content:      {chunk.page_content[:120].strip()}")
        print()

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 6 — Embedding + ChromaDB (first slide only)
# ─────────────────────────────────────────────────────────────────────────────
def test_stage6(chunks):
    print_header("STAGE 6 — Embedding + ChromaDB (first slide only)")
    from ingestion.embedder import get_vectorstore

    if not chunks:
        print("⏭️  Skipping — no chunks from Stage 5.")
        return False

    print("Connecting to ChromaDB and embedding...")
    print("(First embedding may take 1–2 minutes while model loads)\n")

    try:
        vectorstore = get_vectorstore()
        vectorstore.add_documents(chunks)
        vectorstore.persist()

        # Verify by doing a quick search
        results = vectorstore.similarity_search("test", k=1)
        print(f"✅ Chunks stored in ChromaDB successfully")
        print(f"   Verification search returned {len(results)} result(s)")
        return True

    except Exception as e:
        print(f"❌ ChromaDB error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Run all stages
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Ingestion Pipeline — Staged Test")
    print("Each stage tests one component independently.\n")

    # Stage 1
    pptx_files = test_stage1()
    if not pptx_files:
        sys.exit(1)

    # Stage 2
    slides = test_stage2(pptx_files)

    # Stage 3
    slide_images = test_stage3(pptx_files)

    # Stage 4
    vision_desc = test_stage4(slide_images)

    # Stage 5
    chunks = test_stage5(slides, vision_desc)

    # Stage 6
    success = test_stage6(chunks)

    # ── Summary ───────────────────────────────────────────────────────────────
    print_header("SUMMARY")
    stages = {
        "Stage 1 — PPTX scan":        pptx_files is not None,
        "Stage 2 — Text extraction":  slides is not None,
        "Stage 3 — Image export":     slide_images is not None,
        "Stage 4 — LLaVA vision":     vision_desc is not None,
        "Stage 5 — Chunking":         chunks is not None,
        "Stage 6 — ChromaDB embed":   success,
    }

    all_passed = True
    for stage, passed in stages.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon}  {stage}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("✅ All stages passed — safe to run full ingestion.")
        print("   Run: python ingestion/embedder.py")
    else:
        print("⚠️  Fix the failing stages above before running full ingestion.")