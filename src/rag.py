"""Retrieval-augmented recommendation pipeline.

Free-text query -> guardrail -> retrieve knowledge-base entries -> build a taste
profile FROM the retrieved entries -> score the catalog -> verify -> explain with
the retrieved sources. The retrieved data determines the profile, so changing the
knowledge base changes the recommendations.
"""
import logging
import os
from collections import defaultdict
from typing import Dict, List, Optional

from src.guardrails import CRISIS_MESSAGE, is_crisis_query, validate_query, verify_recommendations
from src.recommender import load_songs, recommend_songs
from src.retriever import Retriever, load_knowledge_base

LOG_PATH = "logs/vibefinder.log"
MIN_CONFIDENCE = 0.15
TOP_SOURCES = 3
DEFAULT_PROFILE = {"genre": "pop", "mood": "happy", "energy": 0.6, "likes_acoustic": False}

logger = logging.getLogger("vibefinder")


def setup_logging(path: str = LOG_PATH) -> None:
    if logger.handlers:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def build_profile(hits) -> Dict:
    """Aggregates retrieved entries (weighted by similarity) into a user profile."""
    genre_w, mood_w = defaultdict(float), defaultdict(float)
    energy_sum = acoustic_sum = total = 0.0
    for entry, sim in hits:
        total += sim
        energy_sum += sim * entry["energy"]
        acoustic_sum += sim * (1.0 if entry["acoustic"] else 0.0)
        for g in entry["genres"]:
            genre_w[g] += sim / len(entry["genres"])
        for m in entry["moods"]:
            mood_w[m] += sim / len(entry["moods"])
    profile = {"energy": round(energy_sum / total, 2), "likes_acoustic": acoustic_sum / total > 0.5}
    if genre_w:
        profile["genre"] = max(genre_w, key=genre_w.get)
    if mood_w:
        profile["mood"] = max(mood_w, key=mood_w.get)
    return profile


class VibeFinder:
    def __init__(self, songs_path: str = "data/songs.csv", kb_path: str = "data/knowledge_base.json"):
        setup_logging()
        self.songs = load_songs(songs_path)
        try:
            self.retriever: Optional[Retriever] = Retriever(load_knowledge_base(kb_path))
        except (OSError, ValueError) as exc:
            logger.error("knowledge base unavailable, using fallback: %s", exc)
            self.retriever = None

    def recommend(self, query, k: int = 5) -> Dict:
        ok, cleaned = validate_query(query)
        if not ok:
            logger.warning("rejected query %r: %s", query, cleaned)
            return {"status": "invalid", "message": cleaned, "recommendations": [], "confidence": 0.0}

        if is_crisis_query(cleaned):
            logger.warning("safety guardrail triggered")
            return {"status": "safety", "message": CRISIS_MESSAGE, "recommendations": [], "confidence": 0.0}

        if self.retriever is None:
            return self._fallback(cleaned, k, "knowledge base unavailable")

        hits = self.retriever.search(cleaned, top_n=TOP_SOURCES)
        confidence = round(min(1.0, hits[0][1]), 2) if hits else 0.0
        logger.info("query=%r confidence=%.2f sources=%s", cleaned, confidence, [e["id"] for e, _ in hits])
        if confidence < MIN_CONFIDENCE:
            return {"status": "low_confidence", "confidence": confidence, "recommendations": [], "sources": [],
                    "message": "I couldn't match that to a genre, mood, or situation I know. "
                               "Try e.g. 'chill music for studying' or 'high energy workout'."}

        profile = build_profile(hits)
        recs = verify_recommendations(recommend_songs(profile, self.songs, k=k), self.songs)
        sources = [{"id": e["id"], "title": e["title"], "similarity": round(s, 2)} for e, s in hits]
        why = "; ".join(s["title"] for s in sources)
        results = [{"title": s["title"], "artist": s["artist"], "score": round(sc, 2),
                    "explanation": f"{ex} [profile from: {why}]"} for s, sc, ex in recs]
        logger.info("profile=%s top=%s", profile, [r["title"] for r in results])
        return {"status": "ok", "confidence": confidence, "profile": profile, "sources": sources,
                "recommendations": results}

    def _fallback(self, query: str, k: int, reason: str) -> Dict:
        recs = recommend_songs(DEFAULT_PROFILE, self.songs, k=k)
        return {"status": "fallback", "confidence": 0.0, "message": f"Using default profile ({reason}).",
                "profile": DEFAULT_PROFILE, "sources": [],
                "recommendations": [{"title": s["title"], "artist": s["artist"], "score": round(sc, 2),
                                     "explanation": ex} for s, sc, ex in recs]}
