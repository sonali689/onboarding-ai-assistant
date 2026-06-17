import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings 
from langchain_core.documents import Document

from config import (
    CHROMA_DB_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
    PPTX_FOLDER,
)
from ingestion.pptx_extractor import scan_pptx_files, extract_slide_data
from ingestion.slide_exporter import export_slides_as_images
from ingestion.vision_describer import describe_slide_image
from ingestion.chunker import chunk_slide_document


def get_vectorstore() -> Chroma:
    """
    Initialise and return ChromaDB vectorstore.
    Used by both ingestion (write) and query pipeline (read).
    """
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR,
    )
    return vectorstore


def already_ingested(vectorstore: Chroma, filename: str) -> bool:
    """
    Check if a file was already ingested into ChromaDB.
    Compares by filename so re-running skips existing files.
    """
    try:
        results = vectorstore.get(
            where={"source": filename},
            limit=1,
        )
        return len(results["ids"]) > 0
    except Exception:
        return False


def get_ingested_files(vectorstore: Chroma) -> set[str]:
    """
    Return a set of all filenames already stored in ChromaDB.
    Used to show a summary of what will be skipped before processing.
    """
    try:
        results = vectorstore.get()
        filenames = set()
        for meta in results["metadatas"]:
            if meta and "source" in meta:
                filenames.add(meta["source"])
        return filenames
    except Exception:
        return set()


def run_pptx_ingestion(vectorstore: Chroma) -> tuple[int, list[str]]:
    """
    Process all PPTX files and store chunks in ChromaDB.
    Skips files that are already ingested.
    Returns (total_chunks_added, failed_files).
    """
    print("\n" + "=" * 60)
    print("PPTX INGESTION")
    print("=" * 60)

    pptx_files = scan_pptx_files()
    if not pptx_files:
        print("No PPTX files found. Check PPTX_FOLDER in config.py")
        return 0, []

    # ── Checkpoint: find what's already in ChromaDB ───────────────────────────
    ingested = get_ingested_files(vectorstore)
    new_files = [
        f for f in pptx_files
        if os.path.basename(f) not in ingested
    ]
    skipped = len(pptx_files) - len(new_files)

    print(f"Total PPTX files     : {len(pptx_files)}")
    print(f"Already ingested     : {skipped} files (skipping)")
    print(f"New files to process : {len(new_files)} files")

    if not new_files:
        print(" Nothing new to ingest.")
        return 0, []

    total_chunks = 0
    failed_files = []

    for pptx_path in new_files:
        filename  = os.path.basename(pptx_path)
        subfolder = os.path.basename(os.path.dirname(pptx_path))
        print(f"\n {subfolder} / {filename}")

        try:
            # Step 1 — Extract text from slides
            slides = extract_slide_data(pptx_path)
            if not slides:
                print(f"    No slides extracted, skipping.")
                failed_files.append(filename)
                continue
            print(f"  Slides found: {len(slides)}")

            # Step 2 — Export slide images
            slide_images = export_slides_as_images(pptx_path)
            image_lookup = {num: path for num, path in slide_images}

            # Step 3 — Process each slide
            all_chunks: list[Document] = []

            for slide_data in slides:
                slide_num = slide_data["slide_number"]

                # Step 4 — Vision description
                image_path  = image_lookup.get(slide_num, "")
                vision_desc = ""
                if image_path and os.path.exists(image_path):
                    vision_desc = describe_slide_image(image_path)

                # Step 5 — Chunk
                chunks = chunk_slide_document(slide_data, vision_desc)
                all_chunks.extend(chunks)

            # Step 6 — Embed and store
            if all_chunks:
                vectorstore.add_documents(all_chunks)
                total_chunks += len(all_chunks)
                print(f"   Chunks created and stored: {len(all_chunks)}")
            else:
                print(f"    No chunks generated for this file.")
                failed_files.append(filename)

        except Exception as e:
            print(f"   Error processing {filename}: {e}")
            failed_files.append(filename)
            continue

    return total_chunks, failed_files


def run_pdf_ingestion(vectorstore: Chroma) -> tuple[int, list[str]]:
    """
    Process all PDF files and store chunks in ChromaDB.
    Skips files that are already ingested.
    Returns (total_chunks_added, failed_files).
    Skips silently if PyMuPDF is not installed.
    """
    print("\n" + "=" * 60)
    print("PDF INGESTION")
    print("=" * 60)

    # Graceful skip if PyMuPDF not installed
    try:
        from ingestion.pdf_extractor import (
            scan_pdf_files,
            extract_pdf_slide_data,
            export_pdf_pages_as_images,
        )
    except ImportError:
        print("  PyMuPDF not installed — skipping PDF ingestion.")
        print("   To enable: pip install PyMuPDF")
        return 0, []

    pdf_files = scan_pdf_files(PPTX_FOLDER)
    if not pdf_files:
        print("  No PDF files found — skipping.")
        return 0, []

    # ── Checkpoint: find what's already in ChromaDB ───────────────────────────
    ingested = get_ingested_files(vectorstore)
    new_files = [
        f for f in pdf_files
        if os.path.basename(f) not in ingested
    ]
    skipped = len(pdf_files) - len(new_files)

    print(f"Total PDF files      : {len(pdf_files)}")
    print(f"Already ingested     : {skipped} files (skipping)")
    print(f"New files to process : {len(new_files)} files")

    if not new_files:
        print(" Nothing new to ingest.")
        return 0, []

    total_chunks = 0
    failed_files = []

    for pdf_path in new_files:
        filename  = os.path.basename(pdf_path)
        subfolder = os.path.basename(os.path.dirname(pdf_path))
        print(f"\n {subfolder} / {filename}")

        try:
            # Step 1 — Extract text from pages
            pages = extract_pdf_slide_data(pdf_path)
            if not pages:
                print(f"    No pages extracted, skipping.")
                failed_files.append(filename)
                continue
            print(f"  Pages found: {len(pages)}")

            # Step 2 — Export page images
            page_images  = export_pdf_pages_as_images(pdf_path)
            image_lookup = {num: path for num, path in page_images}

            # Step 3 — Process each page
            all_chunks: list[Document] = []

            for page_data in pages:
                page_num = page_data["slide_number"]

                # Step 4 — Vision description
                image_path  = image_lookup.get(page_num, "")
                vision_desc = ""
                if image_path and os.path.exists(image_path):
                    vision_desc = describe_slide_image(image_path)

                # Step 5 — Chunk
                chunks = chunk_slide_document(page_data, vision_desc)
                all_chunks.extend(chunks)

            # Step 6 — Embed and store
            if all_chunks:
                vectorstore.add_documents(all_chunks)
                total_chunks += len(all_chunks)
                print(f"   Chunks created and stored: {len(all_chunks)}")
            else:
                print(f"    No chunks generated for this file.")
                failed_files.append(filename)

        except Exception as e:
            print(f"   Error processing {filename}: {e}")
            failed_files.append(filename)
            continue

    return total_chunks, failed_files


def run_ingestion():
    """
    Main entry point — processes all PPTX and PDF files
    and stores everything in ChromaDB.
    Re-running is safe — already ingested files are skipped automatically.
    """
    print("=" * 60)
    print("Starting bilingual ingestion pipeline")
    print("=" * 60)

    vectorstore = get_vectorstore()

    # Show what's already in the database
    existing = get_ingested_files(vectorstore)
    print(f"Files already in ChromaDB: {len(existing)}")

    # ── PPTX ingestion ────────────────────────────────────────────────────────
    pptx_chunks, pptx_failed = run_pptx_ingestion(vectorstore)

    # ── PDF ingestion ─────────────────────────────────────────────────────────
    pdf_chunks, pdf_failed = run_pdf_ingestion(vectorstore)

    # ── Final summary ─────────────────────────────────────────────────────────
    total_chunks = pptx_chunks + pdf_chunks
    all_failed   = pptx_failed + pdf_failed

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"  PPTX chunks stored : {pptx_chunks}")
    print(f"  PDF  chunks stored : {pdf_chunks}")
    print(f"  Total new chunks   : {total_chunks}")

    if all_failed:
        print(f"\n    Failed files ({len(all_failed)}):")
        for f in all_failed:
            print(f"     {f}")
    else:
        if total_chunks > 0:
            print(f"\n   All new files processed successfully.")
        else:
            print(f"\n   No new files — database is up to date.")

    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()