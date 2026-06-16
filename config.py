"""
Configuration file for Bilingual RAG Chatbot for Employee Onboarding.
Single source of truth for all configuration values.
No logic - only constants.
"""

# ============================================================================
# FILE PATHS
# ============================================================================
PPTX_FOLDER = "data/training_manuals/"
SLIDE_IMAGE_FOLDER = "data/slide_images/"

# ============================================================================
# VECTOR DATABASE (ChromaDB)
# ============================================================================
CHROMA_DB_DIR = "chroma_db/"
CHROMA_COLLECTION_NAME = "onboarding_bilingual"

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================
OLLAMA_BASE_URL = "http://localhost:11434"

# Model names for Ollama
QWEN2_MODEL = "llama3.1:8b"
LLAVA_MODEL = "llava:latest"
EMBEDDING_MODEL = "jeffh/intfloat-multilingual-e5-large:f16"

# ============================================================================
# TEXT CHUNKING
# ============================================================================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ============================================================================
# RETRIEVAL
# ============================================================================
TOP_K = 10

# ============================================================================
# SLIDE EXPORT
# ============================================================================
SLIDE_EXPORT_DPI = 150
