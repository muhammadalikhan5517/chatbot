"""
Web search tool — DuckDuckGo HTML scraping (no SDK needed).
Fallback: returns empty string on any failure.
"""
import requests
import re
from urllib.parse import quote_plus


def search_web(query: str, bq_specific: bool = True, max_results: int = 4) -> str:
    """
    DuckDuckGo se search results fetch karta hai.
    Returns formatted string, empty on failure.
    """
    try:
        if bq_specific:
            search_query = f"Bano Qabil {query} 2025 2026"
        else:
            search_query = query

        encoded = quote_plus(search_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return ""

        # Extract results using regex
        results = re.findall(
            r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>([^<]+)</a>',
            resp.text,
            re.DOTALL
        )

        if not results:
            return ""

        parts = []
        for i, (href, title, snippet) in enumerate(results[:max_results]):
            title = title.strip()
            snippet = snippet.strip()
            if snippet:
                parts.append(f"• {title}: {snippet}")

        return "\n".join(parts).strip()

    except Exception as e:
        print(f"[WebSearch Error] {e}")
        return ""
