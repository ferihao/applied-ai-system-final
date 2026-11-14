from src.agent import VibeAgent
from src.rag import VibeFinder


def test_agent_recovers_from_typos():
    f = VibeFinder()
    assert f.recommend("heavey metl workot")["status"] == "low_confidence"
    r = VibeAgent(f).run("heavey metl workot")
    assert r["status"] == "ok" and r["recommendations"]
    assert any(t["tool"] == "correct_spelling" for t in r["trace"])


def test_agent_asks_when_it_cannot_recover():
    r = VibeAgent().run("tunes for jogging")
    assert r["status"] == "needs_clarification" and "?" in r["message"] and r["recommendations"] == []


def test_agent_never_retries_around_guardrails():
    r = VibeAgent().run("I want to kill myself")
    assert r["status"] == "safety" and not any(t["tool"] == "recommend" and t["phase"] == "act" and t["step"] > 2 for t in r["trace"])
    assert VibeAgent().run("")["status"] == "invalid"


def test_agent_verifies_and_traces():
    r = VibeAgent().run("chill music for studying")
    assert r["verified"] is True
    assert [t["phase"] for t in r["trace"]][0] == "plan" and r["trace"][-1]["phase"] == "check"


def test_song_source_handles_song_named_queries():
    with_src = VibeFinder().recommend("songs similar to Storm Runner")
    without = VibeFinder(use_song_source=False).recommend("songs similar to Storm Runner")
    assert without["status"] == "low_confidence"
    assert with_src["status"] == "ok" and "Storm Runner" not in [r["title"] for r in with_src["recommendations"]]
