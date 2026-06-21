"""
Reset ChromaDB and re-ingest all training materials.

Run this ONCE after updating chunking parameters (chunk_size, overlap, etc.)
to replace old fragments with properly-sized chunks.

Usage:
    python reset_and_reingest.py

This will:
  1. Delete the existing chroma_db/ folder
  2. Run full ingestion with the new parameters
  3. Print a summary of what was processed
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CHROMA_DB_DIR


def main():
    print("=" * 60)
    print("  RESET AND RE-INGEST")
    print("=" * 60)

    # ── Step 1: Delete existing ChromaDB ──────────────────────────────
    chroma_path = os.path.abspath(CHROMA_DB_DIR)

    if os.path.exists(chroma_path):
        print(f"\n  Deleting existing ChromaDB at: {chroma_path}")
        try:
            shutil.rmtree(chroma_path)
            print("  Deleted successfully.")
        except Exception as e:
            print(f"  ERROR deleting ChromaDB: {e}")
            print("  Try closing any running API server first.")
            sys.exit(1)
    else:
        print(f"\n  No existing ChromaDB found at: {chroma_path}")
        print("  Will create fresh database.")

    # ── Step 2: Run full ingestion ────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Starting fresh ingestion with updated parameters...")
    print("=" * 60)

    from config import CHUNK_SIZE, CHUNK_OVERLAP
    print(f"\n  Chunk size:    {CHUNK_SIZE} chars")
    print(f"  Chunk overlap: {CHUNK_OVERLAP} chars")
    print()

    from ingestion.embedder import run_ingestion
    run_ingestion()

    print("\n" + "=" * 60)
    print("  RE-INGESTION COMPLETE")
    print("=" * 60)
    print("\n  You can now restart the API server and test queries.")
    print("  The assistant should give much better answers now.\n")


if __name__ == "__main__":
    main()
