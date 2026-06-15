import sys
import os
import re
import unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query.qa_chain import ask
from config import PPTX_FOLDER, SLIDE_IMAGE_FOLDER

app = FastAPI(title="Autoliv Onboarding Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request model ──────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str


# ── Helper ─────────────────────────────────────────────────────────────────────

def sanitize_for_lookup(name: str) -> str:
    """Same sanitizer as slide_exporter.py — reconstructs image filename."""
    name = name.replace("・", "_")
    name = name.replace("＆", "and")
    name = name.replace("　", "_")
    name = name.replace("·", "_")
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\-_.]", "_", name)
    return name.strip("_")


# ── RAG endpoint ───────────────────────────────────────────────────────────────

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


# ── File serving ───────────────────────────────────────────────────────────────

@app.get("/api/file/{filename}")
async def serve_file(filename: str):
    """
    Serve the actual PPTX or PDF from training_manuals.
    PDF  → inline in browser (jumps to correct page via #page anchor)
    PPTX → download and open in PowerPoint
    """
    found_path = None

    for root, dirs, files in os.walk(PPTX_FOLDER):
        for f in files:
            if f == filename:
                found_path = os.path.join(root, f)
                break
        if found_path:
            break

    if not found_path or not os.path.exists(found_path):
        return JSONResponse(
            {"error": f"File not found: {filename}"},
            status_code=404,
        )

    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return FileResponse(
            found_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control":       "public, max-age=3600",
            },
        )
    else:
        return FileResponse(
            found_path,
            media_type=(
                "application/vnd.openxmlformats-officedocument"
                ".presentationml.presentation"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control":       "public, max-age=3600",
            },
        )


@app.get("/api/slide/{filename}/{slide_number}")
async def get_slide_image(filename: str, slide_number: int):
    """Serve a slide PNG preview image."""
    base      = os.path.splitext(filename)[0]
    safe_base = sanitize_for_lookup(base)

    image_filename = f"{safe_base}_slide_{slide_number:03d}.png"
    image_path     = os.path.join(SLIDE_IMAGE_FOLDER, image_filename)

    if not os.path.exists(image_path):
        if os.path.exists(SLIDE_IMAGE_FOLDER):
            prefix  = f"{safe_base}_slide_{slide_number:03d}"
            matches = [
                f for f in os.listdir(SLIDE_IMAGE_FOLDER)
                if f.startswith(prefix) and f.endswith(".png")
            ]
            if matches:
                image_path = os.path.join(SLIDE_IMAGE_FOLDER, matches[0])
            else:
                return JSONResponse(
                    {"error": f"Slide image not found: {image_filename}"},
                    status_code=404,
                )
        else:
            return JSONResponse(
                {"error": "Slide images folder not found"},
                status_code=404,
            )

    return FileResponse(
        image_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check — used by frontend to show Ready/Offline status."""
    return {"status": "running"}


# ── Serve built React app in production ───────────────────────────────────────
dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount(
        "/",
        StaticFiles(directory=dist_path, html=True),
        name="frontend",
    )