from src.guardrails import validate_query, verify_recommendations
from src.rag import VibeFinder, build_profile
from src.retriever import Retriever, load_knowledge_base


def test_retriever_finds_relevant_entry():
    r = Retriever(load_knowledge_base("data/knowledge_base.json"))
    top = r.search("workout at the gym")[0][0]
    assert top["id"] == "activity-workout"


def test_retriever_no_hits_for_gibberish():
    assert Retriever(load_knowledge_base("data/knowledge_base.json")).search("zzzz qqqq") == []


def test_validate_query_rejects_bad_input():
    for bad in ["", "   ", None, 42, "123 !!", "x" * 500]:
        assert validate_query(bad)[0] is False
    assert validate_query("  chill   lofi ")[1] == "chill lofi"


def test_verify_drops_unknown_songs():
    catalog = [{"id": 1}]
    recs = [({"id": 1}, 1.0, ""), ({"id": 999}, 1.0, "")]
    assert len(verify_recommendations(recs, catalog)) == 1


def test_retrieval_changes_recommendations():
    vf = VibeFinder()
    calm = vf.recommend("sleep", k=1)["recommendations"][0]["title"]
    loud = vf.recommend("workout", k=1)["recommendations"][0]["title"]
    assert calm != loud


def test_profile_uses_retrieved_entries():
    p = build_profile([({"genres": ["jazz"], "moods": [], "energy": 0.4, "acoustic": True}, 1.0)])
    assert p["genre"] == "jazz" and p["likes_acoustic"] is True


def test_low_confidence_and_invalid_status():
    vf = VibeFinder()
    assert vf.recommend("asdfgh qwerty")["status"] == "low_confidence"
    assert vf.recommend("")["status"] == "invalid"


def test_fallback_when_knowledge_base_missing(tmp_path):
    vf = VibeFinder(kb_path=str(tmp_path / "missing.json"))
    r = vf.recommend("chill", k=2)
    assert r["status"] == "fallback" and len(r["recommendations"]) == 2


def test_crisis_query_returns_support_not_songs():
    r = VibeFinder().recommend("I want to kill myself")
    assert r["status"] == "safety" and r["recommendations"] == [] and "988" in r["message"]


def test_negation_is_respected():
    from src.query_parser import parse_query
    assert parse_query("not sad please, something happy") == ("please something happy", "sad")
    assert parse_query("anything but jazz, I want to relax")[1] == "jazz"
    assert parse_query("chill but energetic")[1] == ""
    vf = VibeFinder()
    top = vf.recommend("anything but jazz, I want to relax", k=5)["recommendations"]
    assert all(s["title"] != "Coffee Shop Stories" for s in top)  # the jazz song


def test_multi_genre_request_returns_both_genres():
    vf = VibeFinder()
    titles = {r["title"] for r in vf.recommend("reggae and metal mixed", k=3)["recommendations"]}
    genres = {s["genre"] for s in vf.songs if s["title"] in titles}
    assert {"reggae", "metal"} <= genres


def test_stemming_matches_word_forms():
    from src.retriever import tokenize
    assert tokenize("relaxing") == tokenize("relaxed")
