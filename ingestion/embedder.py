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


def run_ingestion():
    """Main entry point — processes all PPTX files and stores in ChromaDB."""
    print("=" * 60)
    print("Starting bilingual ingestion pipeline")
    print("=" * 60)

    pptx_files = scan_pptx_files()
    if not pptx_files:
        print("❌ No PPTX files found. Check PPTX_FOLDER in config.py")
        return

    vectorstore = get_vectorstore()
    total_chunks = 0

    for pptx_path in pptx_files:
        filename = os.path.basename(pptx_path)
        subfolder = os.path.basename(os.path.dirname(pptx_path))
        print(f"\n📂 {subfolder} / {filename}")

        # Step 1 — Extract text from slides
        slides = extract_slide_data(pptx_path)
        if not slides:
            print(f"  ⚠️  No slides extracted, skipping.")
            continue
        print(f"  Slides found: {len(slides)}")

        # Step 2 — Export slide images
        slide_images = export_slides_as_images(pptx_path)

        # Build a lookup: slide_number → image_path
        image_lookup = {num: path for num, path in slide_images}

        # Step 3 — Process each slide
        all_chunks: list[Document] = []

        for slide_data in slides:
            slide_num = slide_data["slide_number"]

            # Step 4 — Vision description
            image_path = image_lookup.get(slide_num, "")
            vision_desc = ""
            if image_path and os.path.exists(image_path):
                vision_desc = describe_slide_image(image_path)

            # Step 5 — Chunk
            chunks = chunk_slide_document(slide_data, vision_desc)
            all_chunks.extend(chunks)

        # Step 6 — Embed and store
        if all_chunks:
            vectorstore.add_documents(all_chunks)
            #vectorstore.persist()
            total_chunks += len(all_chunks)
            print(f"  ✅ Chunks created and stored: {len(all_chunks)}")
        else:
            print(f"  ⚠️  No chunks generated for this file.")

    print("\n" + "=" * 60)
    print(f"✅ Ingestion complete. Total chunks stored: {total_chunks}")
    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()
