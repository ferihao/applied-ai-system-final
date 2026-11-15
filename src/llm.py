"""Optional generation step: a local Ollama model writes the explanations.

The model never chooses or ranks songs. It only phrases an explanation for songs the
rule-based scorer already picked, using ONLY the retrieved knowledge-base text. A grounding
guardrail rejects any explanation that mentions a different catalog song, and the system
falls back to the template explanation if Ollama is unavailable or the output is unusable.
"""
import json
import logging
import os
import urllib.request
from typing import Dict, List, Optional

logger = logging.getLogger("vibefinder")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
MAX_EXPLANATION_CHARS = 300
STYLES = ("default", "concise")

# Specialization: a constrained style taught with few-shot examples (invented songs, so nothing
# here can leak into real recommendations). Measured against the default in src/style_eval.py.
CONCISE_RULES = (
    "STYLE RULES: write exactly ONE sentence of at most 18 words per song. It must state the song's "
    "energy level using the words 'low energy', 'medium energy' or 'high energy', and tie it to the "
    "user's request. No filler such as 'this song' or 'fits the request'."
)
CONCISE_EXAMPLES = [
    ("User request: calm music for reading\n\nRetrieved context:\n- Mood: peaceful: peaceful serene quiet\n\n"
     "Recommended songs:\n- title: \"Example Alpha\" | artist: A | genre: ambient | mood: peaceful | "
     "energy: 0.2 (low energy) | score reasons: mood match\n\nExplain why each song fits the request.",
     '{"explanations": {"Example Alpha": "Serene and low energy, it keeps your reading calm and undisturbed."}}'),
    ("User request: pump me up at the gym\n\nRetrieved context:\n- Situation: workout: gym lifting cardio\n\n"
     "Recommended songs:\n- title: \"Example Beta\" | artist: B | genre: rock | mood: intense | "
     "energy: 0.9 (high energy) | score reasons: genre match\n\nExplain why each song fits the request.",
     '{"explanations": {"Example Beta": "Pounding, high energy rock built to push you through every set."}}'),
    ("User request: something for cooking dinner\n\nRetrieved context:\n- Situation: cooking: dinner kitchen\n\n"
     "Recommended songs:\n- title: \"Example Gamma\" | artist: C | genre: jazz | mood: relaxed | "
     "energy: 0.5 (medium energy) | score reasons: mood match\n\nExplain why each song fits the request.",
     '{"explanations": {"Example Gamma": "Smooth, medium energy jazz that keeps the kitchen relaxed and moving."}}'),
]


def energy_label(energy: float) -> str:
    return "low energy" if energy < 0.4 else "medium energy" if energy < 0.7 else "high energy"

SYSTEM_PROMPT = (
    "You write short explanations for music recommendations. Use ONLY the retrieved context and song "
    "facts you are given. Never mention any song, artist or fact that is not provided. "
    "Answer as JSON: {\"explanations\": {\"<exact song title>\": \"<one or two sentences>\"}}."
)


def _chat(messages: List[Dict], timeout: int = 120) -> str:
    """Calls Ollama's chat API. Temperature 0 and a fixed seed keep output repeatable."""
    body = json.dumps({"model": OLLAMA_MODEL, "messages": messages, "stream": False, "format": "json",
                       "options": {"temperature": 0, "seed": 7}}).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())["message"]["content"]


def is_grounded(title: str, text: str, catalog_titles: List[str]) -> bool:
    """Guardrail: non-empty, short, and mentions no OTHER catalog song."""
    if not text or len(text) > MAX_EXPLANATION_CHARS:
        return False
    low = text.lower()
    return not any(t.lower() in low for t in catalog_titles if t != title)


def build_messages(user: str, style: str) -> List[Dict]:
    if style == "concise":
        msgs = [{"role": "system", "content": SYSTEM_PROMPT + " " + CONCISE_RULES}]
        for q, a in CONCISE_EXAMPLES:
            msgs += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
        return msgs + [{"role": "user", "content": user}]
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def generate_explanations(query: str, context: List[str], recs: List[Dict],
                          catalog_titles: List[str], style: str = "default") -> Optional[Dict[str, str]]:
    """Returns {title: explanation} for the songs that passed the grounding check (may be partial)."""
    facts = "\n".join(f"- title: \"{r['title']}\" | artist: {r['artist']} | genre: {r['genre']} | "
                      f"mood: {r['mood']} | energy: {r['energy']} ({energy_label(r['energy'])}) | score reasons: {r['why']}" for r in recs)
    user = (f"User request: {query}\n\nRetrieved context:\n" + "\n".join(f"- {c}" for c in context)
            + f"\n\nRecommended songs:\n{facts}\n\nExplain why each song fits the request. "
            "Use the exact title text (without the artist) as each JSON key.")
    try:
        raw = _chat(build_messages(user, style))
        parsed = json.loads(raw)
        data = parsed.get("explanations", parsed)  # tolerate a missing wrapper key
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object of title -> explanation")
    except Exception as exc:  # network, timeout, bad JSON, missing key: never crash the pipeline
        logger.warning("LLM explanation unavailable, using templates: %s", exc)
        return None
    valid_titles = {r["title"] for r in recs}
    out = {}
    for key, text in data.items():
        title = next((t for t in valid_titles if key == t or key.startswith(t + " by ")), None)
        if title and isinstance(text, str) and is_grounded(title, text.strip(), catalog_titles):
            out[title] = text.strip()
        else:
            logger.warning("LLM explanation rejected by grounding guardrail for %r", key)
    return out
