import os, re, json
from typing import Dict, List

MIN_Q = int(os.getenv('MIN_QUERY_CHARS', 8))
MAX_A = int(os.getenv('MAX_ANSWER_CHARS', 4000))
GROUND_MIN = float(os.getenv('GROUNDING_MIN_SCORE', 0.25))

PII_PATTERNS = {
'email': re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}"),
'phone': re.compile(r"\+?\d[\d\s\-]{7,}\d"),
'iban': re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}"),
}
PROFANITY = re.compile(r"\b(merde|con|pute|fdp|batard|enculé)\b", re.I)
INJECTION = re.compile(r"(ignore|disregard|bypass|contradict|réécris|oublie)\s+(les|toutes?)\s+instructions", re.I)

SAFE_TOPICS_DENYLIST = [
re.compile(r"\b(malware|ransomware|fabriquer\s+explosif|pirater)\b", re.I),
]

def validate_query(q: str) -> Dict:
    if not q or len(q.strip()) < MIN_Q:
        return {"ok": False, "reason": "query_too_short"}
    if INJECTION.search(q):
        return {"ok": False, "reason": "prompt_injection"}
    for pat in SAFE_TOPICS_DENYLIST:
        if pat.search(q):
            return {"ok": False, "reason": "unsafe_topic"}
    return {"ok": True}

def redact_pii(text: str) -> str:
    for name, pat in PII_PATTERNS.items():
        text = pat.sub(f"[REDACTED-{name}]", text)
    return text

def mask_profanity(text: str) -> str:
    return PROFANITY.sub(lambda m: m.group(0)[0] + "***", text)

def enforce_max_len(text: str) -> str:
    return text[:MAX_A]

def grounding_guard(answer: str, ctx_docs: List[Dict]) -> Dict:
    # vérifie qu’on cite au moins une source et que le score moyen est suffisant
    if not ctx_docs:
        return {"ok": False, "reason": "no_context"}
    avg = sum(d.get('score', 0) for d in ctx_docs) / max(1, len(ctx_docs))
    if avg < GROUND_MIN:
        return {"ok": False, "reason": "low_grounding", "avg": avg}
    # exige au moins une citation [#id]
    if not re.search(r"\[#\d+\]", answer):
        return {"ok": False, "reason": "missing_citations"}
    return {"ok": True}

def output_filters(text: str) -> str:
    text = redact_pii(text)
    text = mask_profanity(text)
    text = enforce_max_len(text)
    return text