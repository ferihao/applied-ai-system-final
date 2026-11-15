"""Retrieval-augmented recommendation pipeline.

Free-text query -> guardrail -> retrieve knowledge-base entries -> build a taste
profile FROM the retrieved entries -> score the catalog -> verify -> explain with
the retrieved sources. The retrieved data determines the profile, so changing the
knowledge base changes the recommendations.
"""
import json
import logging
import os
from collections import defaultdict
from typing import Dict, List, Optional

from src import llm
from src.guardrails import CRISIS_MESSAGE, is_crisis_query, validate_query, verify_recommendations
from src.query_parser import parse_query
from src.recommender import load_songs, recommend_songs
from src.retriever import Retriever, load_knowledge_base

LOG_PATH = "logs/vibefinder.log"
MIN_CONFIDENCE = 0.15
SONG_MATCH_MIN = 0.50   # otherwise the query must name the song's title outright
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
    for key, weights in (("genre", genre_w), ("mood", mood_w)):
        if weights:
            top = max(weights.values())
            keep = sorted((w for w in weights if weights[w] >= 0.6 * top), key=weights.get, reverse=True)[:3]
            profile[key] = keep[0]
            profile[key + "s"] = keep
    return profile


def rank_songs(profile: Dict, songs: List[Dict], k: int, excluded_genres=(), excluded_moods=()) -> List:
    """Scores every song under each wanted genre/mood combo (max wins) and drops excluded ones."""
    best = {}
    for genre in profile.get("genres") or [None]:
        for mood in profile.get("moods") or [None]:
            prefs = {"energy": profile["energy"], "likes_acoustic": profile["likes_acoustic"]}
            if genre:
                prefs["genre"] = genre
            if mood:
                prefs["mood"] = mood
            for song, score, why in recommend_songs(prefs, songs, k=len(songs)):
                if song["id"] not in best or score > best[song["id"]][1]:
                    best[song["id"]] = (song, score, why)
    ranked = [r for r in best.values()
              if r[0]["genre"] not in excluded_genres and r[0]["mood"] not in excluded_moods]
    ranked.sort(key=lambda r: r[1], reverse=True)
    return ranked[:k]


def song_entries(songs: List[Dict], notes: Dict[str, str]) -> List[Dict]:
    """Turns catalog songs plus hand-written notes into retrievable documents (source #2)."""
    return [{"id": f"song-{s['id']}", "title": f"Song: {s['title']}",
             "text": f"{s['title']} {s['artist']} {s['genre']} {s['mood']} {notes.get(str(s['id']), '')}",
             "genres": [s["genre"]], "moods": [s["mood"]], "energy": s["energy"],
             "acoustic": s["acousticness"] > 0.6, "song_id": s["id"]} for s in songs]


class VibeFinder:
    def __init__(self, songs_path: str = "data/songs.csv", kb_path: str = "data/knowledge_base.json",
                 notes_path: str = "data/song_notes.json", use_song_source: bool = True,
                 use_llm: bool = False):
        setup_logging()
        self.use_llm = use_llm
        self.songs = load_songs(songs_path)
        self.song_retriever: Optional[Retriever] = None
        if use_song_source:
            try:
                with open(notes_path, encoding="utf-8") as f:
                    self.song_retriever = Retriever(song_entries(self.songs, json.load(f)))
            except (OSError, ValueError) as exc:
                logger.warning("song notes unavailable, using knowledge base only: %s", exc)
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

        wanted, avoided = parse_query(cleaned)
        hits = self.retriever.search(wanted, top_n=TOP_SOURCES)
        ex_genres, ex_moods = set(), set()
        if avoided:
            for entry, sim in self.retriever.search(avoided, top_n=2):
                if sim >= MIN_CONFIDENCE:
                    ex_genres.update(entry["genres"] if entry["id"].startswith("genre-") else [])
                    ex_moods.update(entry["moods"] if entry["id"].startswith("mood-") else [])
        seed_song_ids = set()
        if self.song_retriever:  # source #2: a query that names or describes a specific song
            for entry, sim in self.song_retriever.search(wanted, top_n=1):
                named = entry["title"].split(": ", 1)[1].lower() in wanted.lower()
                if named or sim >= SONG_MATCH_MIN:
                    hits = sorted(hits + [(entry, sim)], key=lambda h: h[1], reverse=True)[:TOP_SOURCES]
                    seed_song_ids.add(entry["song_id"])
        confidence = round(min(1.0, hits[0][1]), 2) if hits else 0.0
        logger.info("query=%r wanted=%r avoided=%r confidence=%.2f sources=%s",
                    cleaned, wanted, avoided, confidence, [e["id"] for e, _ in hits])
        if confidence < MIN_CONFIDENCE:
            return {"status": "low_confidence", "confidence": confidence, "recommendations": [], "sources": [],
                    "message": "I couldn't match that to a genre, mood, or situation I know. "
                               "Try e.g. 'chill music for studying' or 'high energy workout'."}

        profile = build_profile(hits)
        # a genre/mood the user excluded can never be a wanted one
        for key in ("genre", "mood"):
            excluded = ex_genres if key == "genre" else ex_moods
            profile[key + "s"] = [v for v in profile.get(key + "s", []) if v not in excluded]
            if profile[key + "s"]:
                profile[key] = profile[key + "s"][0]
            else:
                profile.pop(key, None)
                profile.pop(key + "s", None)
        pool = [x for x in self.songs if x["id"] not in seed_song_ids]  # never recommend the song asked about
        recs = verify_recommendations(rank_songs(profile, pool, k, ex_genres, ex_moods), self.songs)
        sources = [{"id": e["id"], "title": e["title"], "similarity": round(s, 2)} for e, s in hits]
        why = "; ".join(s["title"] for s in sources)
        results = [{"title": s["title"], "artist": s["artist"], "score": round(sc, 2),
                    "explanation": f"{ex} [profile from: {why}]"} for s, sc, ex in recs]
        explanation_source = "template"
        if self.use_llm and results:
            by_title = {x["title"]: x for x in self.songs}
            context = [f"{e['title']}: {e['text']}" for e, _ in hits]
            facts = [{**by_title[r["title"]], "why": r["explanation"].split(" [profile")[0]} for r in results]
            written = llm.generate_explanations(cleaned, context, facts, [x["title"] for x in self.songs])
            if written:
                for r in results:
                    if r["title"] in written:
                        r["explanation"] = f"{written[r['title']]} (score: {r['explanation'].split(' [profile')[0]})"
                        r["explanation_source"] = "llm"
                explanation_source = f"llm ({llm.OLLAMA_MODEL})" if all(r.get("explanation_source") == "llm" for r in results) else "llm partial, template fallback"
            else:
                explanation_source = "template (llm unavailable or rejected)"
        logger.info("profile=%s top=%s explanations=%s", profile, [r["title"] for r in results], explanation_source)
        return {"status": "ok", "confidence": confidence, "profile": profile, "sources": sources,
                "explanation_source": explanation_source,
                "avoided": sorted(ex_genres | ex_moods),
                "recommendations": results}

    def _fallback(self, query: str, k: int, reason: str) -> Dict:
        recs = recommend_songs(DEFAULT_PROFILE, self.songs, k=k)
        return {"status": "fallback", "confidence": 0.0, "message": f"Using default profile ({reason}).",
                "profile": DEFAULT_PROFILE, "sources": [],
                "recommendations": [{"title": s["title"], "artist": s["artist"], "score": round(sc, 2),
                                     "explanation": ex} for s, sc, ex in recs]}
