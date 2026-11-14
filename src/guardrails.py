"""Input and output guardrails for the VibeFinder RAG pipeline."""
from typing import Dict, List, Tuple

MAX_QUERY_CHARS = 300


def validate_query(query) -> Tuple[bool, str]:
    """Returns (ok, cleaned_query_or_error_message)."""
    if not isinstance(query, str):
        return False, "Query must be text."
    cleaned = " ".join(query.split())
    if not cleaned:
        return False, "Query is empty. Describe the mood, genre, or situation you want music for."
    if len(cleaned) > MAX_QUERY_CHARS:
        return False, f"Query is too long (max {MAX_QUERY_CHARS} characters)."
    if not any(ch.isalpha() for ch in cleaned):
        return False, "Query must contain words."
    return True, cleaned


def verify_recommendations(recs: List[Tuple[Dict, float, str]], catalog: List[Dict]) -> List[Tuple[Dict, float, str]]:
    """Drops any recommendation whose song is not actually in the catalog."""
    valid_ids = {s["id"] for s in catalog}
    return [r for r in recs if r[0].get("id") in valid_ids]


CRISIS_TERMS = ("kill myself", "suicide", "suicidal", "end my life", "self harm", "self-harm", "hurt myself")
CRISIS_MESSAGE = ("This sounds like you may be going through something serious. A song list isn't the right tool "
                  "for that. If you're in the US you can call or text 988 (Suicide & Crisis Lifeline); elsewhere, "
                  "please contact local emergency services or a trusted person.")


def is_crisis_query(query: str) -> bool:
    """Detects self-harm language so the system answers with support resources instead of songs."""
    q = query.lower()
    return any(term in q for term in CRISIS_TERMS)
