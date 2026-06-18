import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_KEY_HERE")
SECRET_KEY = os.getenv("SECRET_KEY", "banoqaabil2024")
DB_PATH = os.getenv("DB_PATH", "bq_chatbot.db")
