import os
import gc
from config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL, OLLAMA_BASE_URL
from ingestion.pptx_extractor import scan_pptx_files, extract_slide_data
from ingestion.slide_exporter import export_slides_as_images
from ingestion.vision_describer import describe_slide_image
from ingestion.chunker import chunk_slide_document
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings

def get_vectorstore():
    """Initializes the vector store connection."""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

def run_ingestion():
    """Orchestrates the ingestion pipeline."""
    print("🚀 Starting Ingestion Pipeline...")
    
    # 1. Initialize DB
    vectorstore = get_vectorstore()
    
    # 2. Find all files
    pptx_files = scan_pptx_files()
    if not pptx_files:
        print("❌ No PPTX files found. Check your paths.")
        return

    for pptx_path in pptx_files:
        print(f"\n📂 Processing: {os.path.basename(pptx_path)}")
        
        # 3. Extraction Phase
        slides = extract_slide_data(pptx_path)
        images = export_slides_as_images(pptx_path)
        image_lookup = {num: path for num, path in images}
        
        all_file_chunks = []
        
        # 4. Processing Phase
        for slide in slides:
            print(f"  → Analyzing Slide {slide['slide_number']}...")
            
            # Get visual context
            vision_desc = describe_slide_image(image_lookup.get(slide['slide_number'], ""))
            
            # Create semantic chunks
            chunks = chunk_slide_document(slide, vision_desc)
            all_file_chunks.extend(chunks)
            
        # 5. Load into Vector Database
        if all_file_chunks:
            vectorstore.add_documents(all_file_chunks)
            print(f"  ✅ Stored {len(all_file_chunks)} chunks for this file.")
        
        # Cleanup memory for CPU execution
        gc.collect()

    print("\n🏁 Ingestion Complete!")

if __name__ == "__main__":
    run_ingestion()