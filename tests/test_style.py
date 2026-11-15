from src import llm
from src.style_eval import check, llm_text


def test_concise_style_adds_few_shot_examples_and_rules():
    default = llm.build_messages("U", "default")
    concise = llm.build_messages("U", "concise")
    assert len(default) == 2 and len(concise) == 2 + 2 * len(llm.CONCISE_EXAMPLES)
    assert "STYLE RULES" in concise[0]["content"] and "STYLE RULES" not in default[0]["content"]
    assert concise[-1] == {"role": "user", "content": "U"}


def test_few_shot_examples_never_use_real_catalog_titles():
    from src.recommender import load_songs
    titles = [s["title"] for s in load_songs("data/songs.csv")]
    blob = " ".join(q + a for q, a in llm.CONCISE_EXAMPLES).lower()
    assert not any(t.lower() in blob for t in titles)


def test_style_checker_measures_the_constraints():
    good = check("Serene, low energy folk for a rainy day.")
    assert all([good["one_sentence"], good["max_18_words"], good["states_energy"], good["no_filler"]])
    bad = check("This song fits the request. It is a good match for you and covers many moods and situations nicely.")
    assert not bad["one_sentence"] and not bad["states_energy"] and not bad["no_filler"]
    assert llm_text("Nice. (score: genre match (+2.0))") == "Nice."


def test_energy_label_boundaries():
    assert llm.energy_label(0.2) == "low energy" and llm.energy_label(0.5) == "medium energy" and llm.energy_label(0.9) == "high energy"
