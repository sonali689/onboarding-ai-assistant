import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query.qa_chain import ask

app = FastAPI(title="Autoliv Onboarding Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Run a question through the RAG pipeline."""
    try:
        result = ask(request.question)
        return JSONResponse({
            "answer":      result["answer"],
            "sources":     result["sources"],
            "source_type": result["source_type"],
            "status":      "ok",
        })
    except Exception as e:
        return JSONResponse({
            "answer":      f"An error occurred: {str(e)}",
            "sources":     [],
            "source_type": "general_knowledge",
            "status":      "error",
        }, status_code=500)


@app.get("/health")
async def health():
    """Health check — used by frontend to show Ready/Offline status."""
    return {"status": "running"}


# ── Serve built React app in production ───────────────────────────────────────
# Only mounted if the dist folder exists (after npm run build)
dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount(
        "/",
        StaticFiles(directory=dist_path, html=True),
        name="frontend",
    )