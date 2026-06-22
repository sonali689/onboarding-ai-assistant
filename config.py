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
STANDARD_MODEL  = "qwen2.5:7b"     # fast, reliable, no internal reasoning
EXTENDED_MODEL  = "qwen2.5:14b"     # slower, uses internal reasoning for depth
LLAVA_MODEL     = "llava:latest"
EMBEDDING_MODEL = "jeffh/intfloat-multilingual-e5-large:f16" 

# ============================================================================
# TEXT CHUNKING
# ============================================================================
CHUNK_SIZE = 1500         # ~1 full slide per chunk, preserves coherent meaning
CHUNK_OVERLAP = 200       # enough to keep context across boundaries

# ============================================================================
# RETRIEVAL
# ============================================================================
TOP_K = 8                 # standard mode — fewer but larger, meaningful chunks
TOP_K_EXTENDED = 12       # extended mode — more material for deeper answers

# MMR (Maximal Marginal Relevance) — balances relevance with diversity
MMR_FETCH_K = 25          # candidate pool size for MMR to pick from
MMR_LAMBDA = 0.7          # 0=max diversity, 1=max relevance — 0.7 favors relevance

# ============================================================================
# RELEVANCE FILTERING
# ============================================================================
RELEVANCE_PREVIEW_CHARS = 600   # chars shown to filter LLM per chunk

# ============================================================================
# SLIDE EXPORT
# ============================================================================
SLIDE_EXPORT_DPI = 150
