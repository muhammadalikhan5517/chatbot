"""
Bano Qabil Chatbot — Flask Backend
Sources: PDF RAG + Web Search + Gemini LLM
Database: SQLite (no PostgreSQL needed)
"""
import os
import json
from flask import Flask, request, jsonify, send_from_directory

from backend.database import init_db
from backend.llm import get_gemini_response
from backend.relevance import is_bano_qabil_related, needs_web_search, is_general_tech
from backend.rag import search_docs, sync_knowledge_base  # نئی لائن

from backend.tools import search_web
from backend.memory import save_message, get_history, create_session
from backend.multimodal import analyze_image

# ─── App Setup ───────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="frontend", static_url_path="/static")

# Init DB + RAG on startup
init_db()
try:
    load_documents()
    print("[Startup] RAG ready.")
except Exception as e:
    print(f"[Startup] RAG warning: {e}")


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def root():
    if os.path.exists("frontend/index.html"):
        return send_from_directory("frontend", "index.html")
    return jsonify({
        "message": "Bano Qabil Chatbot v2.0 is running!",
        "endpoints": ["/chat", "/chat/image", "/health", "/session/new"]
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", 1)
    user_id = data.get("user_id", 1)

    if not message:
        return jsonify({
            "response": "Kuch likhein toh main madad kar sakta hoon! 😊",
            "session_id": session_id,
            "sources_used": []
        })

    # ── Relevance Check ──────────────────────────────────────────────────────
    if not is_bano_qabil_related(message):
        out_of_scope = (
            "Main sirf Bano Qabil aur technology se related sawaalon mein "
            "madad kar sakta hoon. Kuch poochna chahte hain? 😊"
        )
        save_message(session_id, user_id, "user", message, is_relevant=False)
        save_message(session_id, user_id, "assistant", out_of_scope)
        return jsonify({
            "response": out_of_scope,
            "session_id": session_id,
            "sources_used": []
        })

    # ── History ──────────────────────────────────────────────────────────────
    history = get_history(session_id)
    sources_used = []

    # ── Source 1: PDF RAG ────────────────────────────────────────────────────
    doc_context = search_docs(message)
    if doc_context:
        sources_used.append("pdf_rag")

    # ── Source 2: Web Search ─────────────────────────────────────────────────
    web_context = ""
    if needs_web_search(message):
        web_context = search_web(message, bq_specific=True)
        if web_context:
            sources_used.append("web_bq")
    elif is_general_tech(message):
        web_context = search_web(message, bq_specific=False)
        if web_context:
            sources_used.append("web_tech")

    # ── Build Enriched Message ───────────────────────────────────────────────
    full_message = message
    if doc_context:
        full_message += f"\n\n[Document Context - BQ Knowledge Base]:\n{doc_context}"
    if web_context:
        full_message += f"\n\n[Web Context - Live Search Results]:\n{web_context}"

    # ── LLM ──────────────────────────────────────────────────────────────────
    response = get_gemini_response(full_message, history)
    sources_used.append("llm_knowledge")

    # ── Save ─────────────────────────────────────────────────────────────────
    save_message(session_id, user_id, "user", message)
    save_message(session_id, user_id, "assistant", response)

    return jsonify({
        "response": response,
        "session_id": session_id,
        "sources_used": sources_used
    })


@app.route("/chat/image", methods=["POST"])
def chat_image():
    question = request.form.get("question", "")
    session_id = int(request.form.get("session_id", 1))
    user_id = int(request.form.get("user_id", 1))

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    image_data = file.read()
    if not image_data:
        return jsonify({"error": "Empty file"}), 400

    response = analyze_image(image_data, question)
    save_message(session_id, user_id, "user", f"[Image] {question}")
    save_message(session_id, user_id, "assistant", response)
    return jsonify({"response": response, "session_id": session_id})


@app.route("/health")
def health():
    from backend.rag import docs_loaded, documents
    from backend.database import DB_AVAILABLE
    return jsonify({
        "status": "ok",
        "message": "Bano Qabil Chatbot v2.0 running!",
        "db": DB_AVAILABLE,
        "rag": {"loaded": docs_loaded, "chunks": len(documents)}
    })


@app.route("/session/new")
def new_session():
    user_id = int(request.args.get("user_id", 1))
    sid = create_session(user_id)
    return jsonify({"session_id": sid})


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)
