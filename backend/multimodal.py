"""
Multimodal module — image analyze via Gemini REST API.
"""
import base64
import requests
from backend.config import GEMINI_API_KEY

VISION_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)


def analyze_image(image_data: bytes, question: str = "") -> str:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_KEY_HERE":
        return "API key configure nahi hua."

    try:
        prompt = question or "Is image mein kya hai? Bano Qabil se related kuch hai toh batao."
        b64 = base64.b64encode(image_data).decode()

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                ]
            }]
        }

        resp = requests.post(
            f"{VISION_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            return (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "Image analyze nahi ho saki.")
            ).strip()
        else:
            print(f"[Vision] API error {resp.status_code}")
            return "Image analyze nahi ho saki. Baad mein try karein."

    except Exception as e:
        print(f"[Vision] Error: {e}")
        return "Image analyze nahi ho saki. 🙏"
