---
license: mit
title: Bano Qabil Chatbot
sdk: docker
emoji: 💻
colorFrom: green
colorTo: blue
pinned: false
---
# Bano Qabil AI Chatbot v2.0

Official AI chatbot for [Bano Qabil](https://banoqabil.pk) IT training program.
Built by Ali — a Bano Qabil student.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python) |
| Database | SQLite (zero setup) |
| AI Model | Gemini 2.5 Flash (REST API) |
| PDF RAG | pdfminer.six |
| Web Search | DuckDuckGo (requests) |

---

## Project Structure

```
bq_chatbot/
├── main.py                  # Flask app — entry point
├── requirements.txt         # Dependencies
├── .env                     # Your secrets (create from .env.example)
├── .env.example             # Template
├── bq_chatbot.db            # SQLite DB (auto-created)
├── knowledge/               # Put your RAG PDFs here
│   └── RAG.pdf
├── frontend/                # Optional: HTML frontend
│   └── index.html
└── backend/
    ├── config.py            # Environment variables
    ├── database.py          # SQLite setup + helpers
    ├── memory.py            # Conversation history
    ├── llm.py               # Gemini 2.5 Flash calls
    ├── rag.py               # PDF knowledge retrieval
    ├── tools.py             # Web search (DuckDuckGo)
    ├── relevance.py         # BQ/tech topic detection
    ├── multimodal.py        # Image analysis
    └── personalization.py   # User profile management
```

---

## Setup (Local)

### 1. Clone & install
```bash
git clone <your-repo>
cd bq_chatbot
pip install -r requirements.txt
```

### 2. Create .env file
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

`.env` contents:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
SECRET_KEY=banoqaabil2024
DB_PATH=bq_chatbot.db
```

### 3. Get Gemini API Key
- Go to: https://aistudio.google.com/app/apikey
- Create API key (free tier available)
- Paste in `.env`

### 4. Add Knowledge PDF (optional)
```bash
# Put your Bano Qabil knowledge PDF in knowledge/ folder
cp your_bq_knowledge.pdf knowledge/RAG.pdf
```

### 5. Run
```bash
python main.py
# Server starts at http://localhost:7860
```

---

## API Endpoints

### POST /chat
```json
{
  "message": "bano qabil mein registration kaise karein?",
  "session_id": 1,
  "user_id": 1
}
```
Response:
```json
{
  "response": "Bano Qabil mein registration ke liye...",
  "session_id": 1,
  "sources_used": ["pdf_rag", "llm_knowledge"]
}
```

### POST /chat/image
```
multipart/form-data
- file: image file
- question: "is mein kya course hai?"
- session_id: 1
- user_id: 1
```

### GET /health
```json
{
  "status": "ok",
  "db": true,
  "rag": {"loaded": true, "chunks": 245}
}
```

### GET /session/new?user_id=1
```json
{"session_id": 5}
```

---

## Deployment (Hugging Face Spaces)

1. Create new Space → Python → Flask
2. Upload all files
3. Add `GEMINI_API_KEY` in Space Settings → Secrets
4. Set `app.py` as entry (or rename `main.py` to `app.py`)
5. Done!

## Deployment (Railway / Render)

```bash
# Procfile
web: python main.py
```
Set `GEMINI_API_KEY` in environment variables.

---

## How It Works

```
User Message
     ↓
Relevance Check (BQ/tech related?)
     ↓ Yes
[Source 1] PDF RAG → search knowledge base
[Source 2] Web Search → DuckDuckGo (time-sensitive queries)
     ↓
Combine context + user message
     ↓
Gemini 2.5 Flash (with system prompt + history)
     ↓
Response → Save to SQLite → Return to user
```

---

## Languages Supported
- Roman Urdu ✓
- Urdu Script ✓  
- English ✓
- Auto-detection ✓

---

## Contact
BQ WhatsApp: 0317-8226244 | Helpline: 021-111-503-504