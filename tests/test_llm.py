import json

from src import llm
from src.rag import VibeFinder

TITLES = ["Library Rain", "Midnight Coding", "Focus Flow"]
RECS = [{"title": "Library Rain", "artist": "Paper Lanterns", "genre": "lofi", "mood": "chill", "energy": 0.35, "why": "x"}]


def test_grounding_rejects_other_catalog_songs():
    assert llm.is_grounded("Library Rain", "Calm and quiet.", TITLES)
    assert not llm.is_grounded("Library Rain", "Better than Focus Flow.", TITLES)
    assert not llm.is_grounded("Library Rain", "", TITLES)
    assert not llm.is_grounded("Library Rain", "x" * 400, TITLES)


def test_hallucinated_or_ungrounded_output_is_dropped(monkeypatch):
    reply = {"explanations": {"Library Rain": "Nice, unlike Focus Flow.", "Made Up Song": "Great."}}
    monkeypatch.setattr(llm, "_chat", lambda m, timeout=120: json.dumps(reply))
    assert llm.generate_explanations("q", ["ctx"], RECS, TITLES) == {}


def test_title_by_artist_keys_and_missing_wrapper_are_accepted(monkeypatch):
    monkeypatch.setattr(llm, "_chat", lambda m, timeout=120: json.dumps({"Library Rain by Paper Lanterns": "Quiet."}))
    assert llm.generate_explanations("q", ["ctx"], RECS, TITLES) == {"Library Rain": "Quiet."}


def test_pipeline_falls_back_to_templates_when_ollama_is_down(monkeypatch):
    def boom(m, timeout=120):
        raise OSError("connection refused")
    monkeypatch.setattr(llm, "_chat", boom)
    r = VibeFinder(use_llm=True).recommend("chill music for studying", k=2)
    assert r["status"] == "ok" and r["explanation_source"].startswith("template")
    assert "genre match" in r["recommendations"][0]["explanation"]


def test_llm_text_is_used_but_ranking_is_unchanged(monkeypatch):
    base = VibeFinder().recommend("chill music for studying", k=2)["recommendations"]
    titles = [r["title"] for r in base]
    monkeypatch.setattr(llm, "_chat", lambda m, timeout=120: json.dumps({"explanations": {t: "Fits studying." for t in titles}}))
    r = VibeFinder(use_llm=True).recommend("chill music for studying", k=2)
    assert [x["title"] for x in r["recommendations"]] == titles
    assert r["recommendations"][0]["explanation"].startswith("Fits studying.")
