import sys
import os
import re
import unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from query.qa_chain import ask
from config import PPTX_FOLDER, SLIDE_IMAGE_FOLDER
from ui.database import (
    init_db, create_user, get_user,
    get_user_chats, upsert_chat, delete_chat,
)
from ui.auth import hash_password, verify_password, create_token, decode_token

init_db()

app = FastAPI(title="Autoliv Onboarding Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ─────────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    history:  list[dict] | None = None


class RegisterRequest(BaseModel):
    email:    str
    name:     str
    password: str


class LoginRequest(BaseModel):
    email:    str
    password: str


class SaveChatRequest(BaseModel):
    chat_id:  str
    title:    str
    messages: str


# ── Auth helper ────────────────────────────────────────────────────────────────

def get_current_user(authorization: Optional[str] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Auth endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    hashed  = hash_password(req.password)
    success = create_user(req.email.lower(), req.name.strip(), hashed)

    if not success:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    token = create_token(req.email.lower())
    return JSONResponse({
        "token": token,
        "user":  {"email": req.email.lower(), "name": req.name.strip()},
    })


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = get_user(req.email.lower())
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_token(req.email.lower())
    return JSONResponse({
        "token": token,
        "user":  {"email": user["email"], "name": user["name"]},
    })


@app.get("/api/auth/verify")
async def verify(authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)
    return JSONResponse({"email": user["email"], "name": user["name"]})


# ── RAG ────────────────────────────────────────────────────────────────────────

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    try:
        result = ask(request.question, request.history)
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


# ── Chat history ───────────────────────────────────────────────────────────────

@app.get("/api/chats")
async def list_chats(authorization: Optional[str] = Header(default=None)):
    user  = get_current_user(authorization)
    chats = get_user_chats(user["email"])
    return JSONResponse(chats)


@app.post("/api/chats")
async def save_chat_endpoint(
    request: SaveChatRequest,
    authorization: Optional[str] = Header(default=None),
):
    user = get_current_user(authorization)
    upsert_chat(
        user_email=user["email"],
        chat_id=request.chat_id,
        title=request.title,
        messages=request.messages,
    )
    return JSONResponse({"status": "ok"})


@app.delete("/api/chats/{chat_id}")
async def delete_chat_endpoint(
    chat_id: str,
    authorization: Optional[str] = Header(default=None),
):
    get_current_user(authorization)
    delete_chat(chat_id)
    return JSONResponse({"status": "ok"})


# ── File serving ───────────────────────────────────────────────────────────────

def sanitize_for_lookup(name: str) -> str:
    name = name.replace("・", "_")
    name = name.replace("＆", "and")
    name = name.replace("　", "_")
    name = name.replace("·", "_")
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\-_.]", "_", name)
    return name.strip("_")


@app.get("/api/file/{filename}")
async def serve_file(filename: str):
    found_path = None
    for root, dirs, files in os.walk(PPTX_FOLDER):
        for f in files:
            if f == filename:
                found_path = os.path.join(root, f)
                break
        if found_path:
            break

    if not found_path or not os.path.exists(found_path):
        return JSONResponse({"error": f"File not found: {filename}"}, status_code=404)

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
    return FileResponse(
        found_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control":       "public, max-age=3600",
        },
    )


@app.get("/api/slide/{filename}/{slide_number}")
async def get_slide_image(filename: str, slide_number: int):
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
                return JSONResponse({"error": f"Not found: {image_filename}"}, status_code=404)
        else:
            return JSONResponse({"error": "Images folder not found"}, status_code=404)

    return FileResponse(
        image_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "running"}


# ── Serve React app in production ──────────────────────────────────────────────

dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")