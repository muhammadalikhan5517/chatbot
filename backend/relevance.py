"""Relevance module — BQ/tech related check."""

BANO_QABIL_KEYWORDS = [
    "bano qabil", "banoqabil", "bq", "alkhidmat", "hafiz naeem",
    "course", "courses", "register", "registration", "apply", "application",
    "fee", "fees", "deposit", "security deposit",
    "web development", "mobile app", "artificial intelligence", "ai", "data science",
    "cyber security", "cybersecurity", "digital marketing", "python", "ui ux", "uiux",
    "graphic design", "video editing", "ecommerce", "amazon", "fba", "devops",
    "sqa", "flutter", "react", "node", "nodejs", "data analytics", "entrepreneurship",
    "freelance", "freelancing", "incubation", "startup", "seed funding",
    "eligibility", "age limit", "interview", "aptitude test", "aptitude",
    "certificate", "certification", "convocation", "campus", "center", "centre",
    "karachi", "lahore", "islamabad", "rawalpindi", "peshawar", "quetta",
    "faisalabad", "multan", "schedule", "timing", "class", "duration",
    "contact", "phone", "whatsapp", "email", "address",
    "free", "muft", "training", "skill", "technology", "tech",
    "job", "career", "coding", "programming", "software", "it", "computer",
    "learn", "learning", "admission", "batch",
    "seekhna", "sikhna", "naukri", "rozgar", "kamai",
    "kab shuru", "naya batch", "agla batch", "kaise apply",
    "داخلہ", "کورس", "فیس", "رجسٹریشن", "سرٹیفکیٹ", "کیمپس",
    "انٹرویو", "ٹیسٹ", "اہلیت", "پروگرام", "تربیت", "مفت",
    "بنو قابل", "بنوقابل", "الخدمت", "سیکھنا", "نوکری", "ٹیکنالوجی",
]

WEB_SEARCH_KEYWORDS = [
    "deadline", "last date", "آخری تاریخ",
    "new batch", "naya batch", "next batch", "agla batch", "نیا بیچ",
    "latest", "2024", "2025", "2026",
    "kab shuru", "kab start", "کب شروع",
    "announce", "announcement", "اعلان",
    "update", "abhi", "aaj", "آج",
    "currently", "right now", "registration open",
]

GENERAL_TECH_KEYWORDS = [
    "kya hota hai", "kya hai", "kia hota", "kia hai",
    "what is", "what are", "explain",
    "samjhao", "بتاؤ", "سمجھاؤ",
    "difference", "fark", "farq", "فرق",
    "better", "behtar", "بہتر",
    "vs", "compare", "comparison",
    "kaise kaam", "how does", "how to",
    "intro", "introduction", "basics",
    "sikhna chahta", "seekhna chahta",
    "kaise seekhun", "kaise shuru",
    "pros cons", "advantages", "disadvantages",
]

GREETING_PATTERNS = [
    "hello", "hi", "hey", "salam", "السلام", "assalam", "aoa", "assalamualaikum",
    "good morning", "good evening", "good afternoon",
    "kya haal", "kaise ho", "theek ho",
    "help", "مدد", "madad",
    "haan", "han", "okay", "ok", "thik",
    "نہیں", "nahi", "شکریہ", "shukriya", "thanks", "thank you",
    "start", "shuru",
]


import re as _re


def _match(keyword: str, text: str) -> bool:
    """
    Short keywords (<=3 chars) require word boundary match.
    Longer keywords can be substring match.
    """
    if len(keyword) <= 3:
        return bool(_re.search(r'\b' + _re.escape(keyword) + r'\b', text))
    return keyword in text


def is_bano_qabil_related(message: str) -> bool:
    msg = message.lower().strip()
    if len(msg) <= 10:
        return True
    for g in GREETING_PATTERNS:
        if _match(g, msg):
            return True
    for kw in BANO_QABIL_KEYWORDS + GENERAL_TECH_KEYWORDS:
        if _match(kw, msg):
            return True
    return False


def needs_web_search(message: str) -> bool:
    msg = message.lower()
    return any(_match(kw, msg) for kw in WEB_SEARCH_KEYWORDS)


def is_general_tech(message: str) -> bool:
    msg = message.lower()
    return any(_match(kw, msg) for kw in GENERAL_TECH_KEYWORDS)
