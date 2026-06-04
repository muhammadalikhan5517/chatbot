from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os, json

from backend.database import get_db, init_db
from backend.memory import (
    get_or_create_user, create_session,
    save_message, get_recent_messages,
    get_user_history, save_feedback,
    save_unanswered, update_user
)
from backend.relevance import is_relevant, get_redirect_message
from backend.rag import search_docs, ingest_all_docs
from backend.tools import web_search, should_search_web, get_current_date
from backend.multimodal import process_image, build_image_prompt
from backend.personalization import build_user_context, detect_language, extract_user_info
from backend.llm import build_prompt, stream_response, stream_with_image
from backend.config import UPLOAD_DIR

# ─── APP SETUP ────────────────────────────────────────

app = FastAPI(title="Bano Qaabil AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

# ─── STARTUP ──────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    ingest_all_docs()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print("🚀 Bano Qaabil Chatbot is LIVE!")

# ─── MODELS ───────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    user_name: str
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    city: Optional[str] = None
    education: Optional[str] = None

class FeedbackRequest(BaseModel):
    session_id: int
    feedback: str  # "positive" or "negative"

# ─── CHAT ENDPOINT ────────────────────────────────────

@app.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):

    # 1. Get or create user
    user = get_or_create_user(
        db=db,
        name=request.user_name,
        city=request.city,
        education=request.education
    )

    # Try to extract info from message
    extracted = extract_user_info(request.message)
    if extracted:
        update_user(db, user.id, **extracted)
        db.refresh(user)

    # 2. Get or create session
    if request.session_id:
        session_id = request.session_id
    else:
        session = create_session(db, user.id)
        session_id = session.id

    # 3. Save user message
    save_message(db, session_id, user.id, "user", request.message)

    # 4. Relevance check
    if not is_relevant(request.message):
        redirect = get_redirect_message(request.message)
        save_message(db, session_id, user.id, "assistant", redirect, is_relevant=False)
        save_unanswered(db, request.message)

        async def redirect_stream():
            yield f"data: {json.dumps({'text': redirect, 'session_id': session_id, 'user_id': user.id})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(redirect_stream(), media_type="text/event-stream")

    # 5. Load memory
    history = get_recent_messages(db, session_id)
    if len(history) <= 1:
        history = get_user_history(db, user.id)

    # 6. RAG search
    rag_context = search_docs(request.message)

    # 7. Web search if needed
    web_context = ""
    if should_search_web(request.message):
        web_context = web_search(request.message)

    # 8. Build user context (personalization)
    user_context = build_user_context(user)
    user_context += f"\nCurrent date: {get_current_date()}"

    # 9. Build prompt
    messages = build_prompt(
        user_message=request.message,
        user_context=user_context,
        rag_context=rag_context,
        web_context=web_context,
        history=history
    )

    # 10. Stream response
    full_response = []

    async def generate():
        async for chunk in stream_response(messages):
            full_response.append(chunk)
            yield f"data: {json.dumps({'text': chunk, 'session_id': session_id, 'user_id': user.id})}\n\n"
        
        # Save complete response
        complete = "".join(full_response)
        save_message(db, session_id, user.id, "assistant", complete)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ─── IMAGE CHAT ───────────────────────────────────────

@app.post("/chat/image")
async def chat_image(
    message: str = Form(...),
    user_name: str = Form(...),
    session_id: Optional[int] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_or_create_user(db, user_name)
    session = create_session(db, user.id) if not session_id else None
    sid = session_id or session.id

    image_bytes = await image.read()
    image_data = process_image(image_bytes)

    if not image_data:
        raise HTTPException(status_code=400, detail="Image processing failed")

    prompt = build_image_prompt(message)
    save_message(db, sid, user.id, "user", f"[Image] {message}")

    full_response = []

    async def generate():
        async for chunk in stream_with_image(prompt, image_data):
            full_response.append(chunk)
            yield f"data: {json.dumps({'text': chunk, 'session_id': sid})}\n\n"
        complete = "".join(full_response)
        save_message(db, sid, user.id, "assistant", complete)
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ─── PDF UPLOAD ───────────────────────────────────────

@app.post("/upload/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    topic: str = Form("general")
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    from backend.rag import ingest_pdf
    ingest_pdf(path, topic)

    return {"message": f"✅ PDF '{file.filename}' uploaded and indexed!"}

# ─── FEEDBACK ─────────────────────────────────────────

@app.post("/feedback")
async def feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    save_feedback(db, req.session_id, "assistant", req.feedback)
    return {"message": "Feedback saved!"}

# ─── HEALTH CHECK ─────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "🟢 Bano Qaabil Chatbot is running!"}
