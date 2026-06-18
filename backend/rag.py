"""
Upgraded RAG module — Pure SQLite + Gemini Embeddings (Smart Semantic Search).
No heavy dependencies, fully integrated with database.py and Gemini API.
"""
import os
import re
import json
import requests
import sqlite3
from backend.config import DB_PATH, GEMINI_API_KEY

# DOCS_PATH ko folder banا diya taake os.listdir sahi kaam kare
DOCS_PATH = "knowledge"

EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "text-embedding-004:embedContent"
)


def _get_db_conn():
    """database.py ki tarah thread-safe SQLite connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_rag_table():
    """SQLite mein chunks aur embeddings ka table banana (Agar nahi bana)."""
    try:
        conn = _get_db_conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS rag_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                chunk_text TEXT,
                embedding TEXT  -- JSON string ki surat mein save hoga
            );
        """)
        conn.commit()
        conn.close()
        print("[RAG DB] RAG knowledge table initialized.")
    except Exception as e:
        print(f"[RAG DB] Table init failed: {e}")


def _get_gemini_embedding(text: str) -> list:
    """Gemini API ka use karte hue text ki embedding (Vector) nikalna."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_KEY_HERE":
        print("[RAG API] Gemini API Key missing for embeddings.")
        return []
    try:
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }
        res = requests.post(
            f"{EMBEDDING_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        if res.status_code == 200:
            return res.json().get("embedding", {}).get("values", [])
        else:
            print(f"[RAG API] Embedding error {res.status_code}: {res.text[:100]}")
            return []
    except Exception as e:
        print(f"[RAG API] Request failed: {e}")
        return []


def _extract_pdf_text(filepath: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(filepath) or ""
    except Exception as e:
        print(f"[RAG] PDF extract error {filepath}: {e}")
        return ""


def _chunk_text(text: str, chunk_size: int = 600, overlap: int = 120) -> list:
    chunks, start = [], 0
    text = text.strip()
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def sync_knowledge_base():
    """
    Folder check karega, agar DB khali hai ya nayi files hain to chunks banaye ga
    aur Gemini se embeddings le kar SQLite mein permanent save karega.
    """
    init_rag_table()
    
    if not os.path.exists(DOCS_PATH):
        print(f"[RAG] Folder not found: {DOCS_PATH}")
        return

    pdfs = [f for f in os.listdir(DOCS_PATH) if f.endswith(".pdf")]
    if not pdfs:
        print("[RAG] No PDFs found in knowledge folder.")
        return

    conn = _get_db_conn()
    c = conn.cursor()

    for fn in pdfs:
        # Check karein agar yeh file pehle se DB mein hai ya nahi
        c.execute("SELECT COUNT(*) as count FROM rag_knowledge WHERE filename = ?", (fn,))
        if c.fetchone()["count"] > 0:
            continue  # Agar file pehle se indexed hai to skip karo

        print(f"[RAG] Processing new file: {fn}...")
        text = _extract_pdf_text(os.path.join(DOCS_PATH, fn))
        if not text:
            continue
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        chunks = _chunk_text(text)

        print(f"[RAG] Generating embeddings for {len(chunks)} chunks of {fn}...")
        for chunk in chunks:
            vector = _get_gemini_embedding(chunk)
            if vector:
                c.execute(
                    "INSERT INTO rag_knowledge (filename, chunk_text, embedding) VALUES (?, ?, ?)",
                    (fn, chunk, json.dumps(vector))
                )
        conn.commit()
        print(f"[RAG] {fn} successfully saved to DB.")
    
    conn.close()


def _cosine_similarity(vecA: list, vecB: list) -> float:
    """Do vectors ke darmiyan similarity score nikalne ka ddesi maths function."""
    if not vecA or not vecB or len(vecA) != len(vecB):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vecA, vecB))
    normA = sum(a * a for a in vecA) ** 0.5
    normB = sum(b * b for b in vecB) ** 0.5
    if normA == 0 or normB == 0:
        return 0.0
    return dot_product / (normA * normB)


def search_docs(query: str, top_k: int = 4) -> str:
    """
    User ki query ki embedding nikal kar SQLite DB mein maujood chunks se
    compare karta hai aur sab se best context return karta hai.
    """
    # Ensure database is synced
    try:
        sync_knowledge_base()
    except Exception as e:
        print(f"[RAG Sync Error] {e}")

    query_vector = _get_gemini_embedding(query)
    if not query_vector:
        return ""  # Agar embedding fail ho jaye fallback to empty string

    try:
        conn = _get_db_conn()
        c = conn.cursor()
        c.execute("SELECT chunk_text, embedding FROM rag_knowledge")
        rows = c.fetchall()
        conn.close()

        if not rows:
            return ""

        scored_chunks = []
        for row in rows:
            chunk_text = row["chunk_text"]
            chunk_vector = json.loads(row["embedding"])
            
            similarity = _cosine_similarity(query_vector, chunk_vector)
            if similarity > 0.35:  # Ek munasib threshold taake be-tuki cheezein na aayein
                scored_chunks.append((similarity, chunk_text))

        # Score ke mutabiq sort karein (Highest first)
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # Top K unique chunks nikalna
        out, seen = [], set()
        for _, chunk in scored_chunks[:top_k * 2]:
            key = chunk[:100]
            if key not in seen:
                seen.add(key)
                out.append(chunk)
            if len(out) >= top_k:
                break

        return "\n---\n".join(out)

    except Exception as e:
        print(f"[RAG Search Error] {e}")
        return ""


# App start hote hi background mein check run karein
try:
    sync_knowledge_base()
except Exception:
    pass
