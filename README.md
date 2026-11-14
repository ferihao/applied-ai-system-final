# VibeFinder RAG: A Retrieval-Augmented Music Recommender

> Type what you want in plain English ("chill music for studying late at night") and get a ranked, explained playlist, grounded in a retrieved knowledge base, protected by guardrails, and measured by an automated evaluation harness.

## Original Project

This capstone extends **VibeFinder 1.0, my Module 3 *Music Recommender Simulation***. VibeFinder 1.0 was a content-based recommender. The user supplied a structured profile (favorite genre, favorite mood, target energy, likes-acoustic), and it scored all 18 songs in `data/songs.csv` with a hand-weighted point system (genre +2.0, mood +1.0, energy closeness up to +1.0, acoustic +0.5). It printed a ranked top-K list with a plain-language reason for every pick. Its full write-up is preserved in [docs/vibefinder_1_0_readme.md](docs/vibefinder_1_0_readme.md).

## What This Version Adds

VibeFinder 1.0 made the user translate their taste into rigid fields, which is a real usability barrier. This version takes **free text** and works out the profile itself.

1. **RAG (retrieval-augmented recommendation):** A TF-IDF retriever searches a 37-entry knowledge base (`data/knowledge_base.json`) of genre, mood and situation descriptions. The retrieved entries, weighted by similarity, *build the taste profile* that drives scoring. Change the knowledge base and the recommendations change. The retrieved sources are cited in every explanation. There is no LLM generation step: the ranking comes from the rule-based scorer and the explanations from templates.
2. **Guardrails:** Input validation, a self-harm safety check, a low-confidence refusal, output verification against the catalog, and a fallback when the knowledge base is unavailable.
3. **Logging:** Every query, retrieved source, confidence and inferred profile goes to `logs/vibefinder.log`.
4. **Reliability system:** Confidence scoring, 19 pytest tests, and an evaluation harness that runs fixed queries five times each.

## Architecture Overview

Source: [diagrams/architecture.mmd](diagrams/architecture.mmd) (Mermaid).

1. **Input:** The query passes an input guardrail (non-empty, has letters, at most 300 characters) and a safety guardrail (self-harm language gets support resources, not songs).
2. **Retrieve:** The `Retriever` (`src/retriever.py`) ranks knowledge-base entries by TF-IDF cosine similarity. The top similarity is the **confidence score**. Below 0.15 the system declines and asks the user to rephrase.
3. **Generate:** `build_profile` (`src/rag.py`) merges the top 3 entries, weighted by similarity, into genre, mood, energy and acoustic preferences. The original scoring engine ranks the catalog against that profile.
4. **Verify and explain:** The output guardrail drops any song not in the catalog. Each explanation lists the score components *and* the retrieved sources behind the profile.
5. **Check:** `src/evaluate.py` and `tests/` exercise the pipeline automatically. A human reviews the results and the evaluation report, then tunes knowledge-base entries, weights and thresholds.

## Setup Instructions

Requires Python 3.9+. No API keys and no network access.

```bash
git clone https://github.com/ferihao/applied-ai-system-final.git
cd applied-ai-system-final
python3 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

python -m src.main "chill music for studying late at night"   # agent + RAG mode
python -m src.main                                             # original 6-profile demo
python -m pytest -q                                            # 19 tests
python -m src.evaluate                                         # regenerates docs/evaluation_results.md
python -m src.agent --save-traces                              # regenerates the traces in docs/ai_interactions.md
```

## Sample Interactions

Real output (trimmed to the first 2 results).

**1. `python -m src.main "high energy workout"`**
```
Query: 'high energy workout'  |  status: ok  |  confidence: 0.38
Inferred profile: {'energy': 0.88, 'likes_acoustic': False, 'genre': 'rock', 'mood': 'energetic'}
  retrieved: Mood: energetic (similarity 0.38)
  retrieved: Situation: workout (similarity 0.34)
1. Storm Runner by Voltline - Score: 2.97
   Because: genre match (+2.0), energy closeness (+0.97) [profile from: Mood: energetic; Situation: workout]
2. Neon Pulse Club by Static Bloom - Score: 2.0
   Because: mood match (+1.0), energy closeness (+1.00) [profile from: Mood: energetic; Situation: workout]
```

**2. `python -m src.main "sad rainy heartbreak"`**
```
Query: 'sad rainy heartbreak'  |  status: ok  |  confidence: 0.39
Inferred profile: {'energy': 0.32, 'likes_acoustic': True, 'genre': 'folk', 'mood': 'sad'}
  retrieved: Mood: sad (similarity 0.39)
  retrieved: Situation: heartbreak (similarity 0.39)
  retrieved: Situation: rainy (similarity 0.36)
1. Riverside Letters by Willow Creek - Score: 3.49
   Because: genre match (+2.0), energy closeness (+0.99), acoustic match (+0.5) [profile from: ...]
2. Lonesome Highway by Delta Moon - Score: 2.48
   Because: mood match (+1.0), energy closeness (+0.98), acoustic match (+0.5) [profile from: ...]
```

**3. `python -m src.main "asdfgh qwerty"`** (guardrail: refuses instead of guessing)
```
Query: 'asdfgh qwerty'  |  status: low_confidence  |  confidence: 0.0
I couldn't match that to a genre, mood, or situation I know. Try e.g. 'chill music for studying' or 'high energy workout'.
```

## Stretch Features

**1. RAG Enhancement: multiple data sources.** Retrieval now searches two sources: the genre/mood/situation knowledge base (`data/knowledge_base.json`) and custom per-song documents (`data/song_notes.json`, hand-written notes merged with each song's catalog attributes). A song is retrieved only if the query names its title or matches it strongly, and the song asked about is never recommended back.

Before/after, real output for `"songs similar to Storm Runner"`:

| | Sources retrieved | Result |
|---|---|---|
| Knowledge base only | none | `low_confidence`: the system refuses, because "Storm Runner" appears in no genre, mood or situation entry |
| With song source | `Song: Storm Runner` (similarity 0.62) | Gym Hero, Neon Pulse Club, Iron Collapse: songs matching Storm Runner's rock/intense/high-energy profile |

I also checked that the extra source doesn't hurt ordinary queries: my first version (similarity threshold 0.30) pulled `Song: Night Drive Loop` into "chill music for studying late at night" because of the word "night". I raised the bar to a title match or similarity 0.50, and the study query went back to its original sources.

**2. Agentic Workflow Enhancement.** `src/agent.py` wraps the pipeline in a plan, act, check loop with three tools (`recommend`, `correct_spelling`, `suggest_options`). It retries a low-confidence query once after fixing likely typos ("heavey metl workot" becomes "heavy metal workout" and returns metal songs, where the plain pipeline refuses). If it still can't tell what the user wants, it asks a clarifying question instead of guessing. It never retries around a guardrail (empty input or self-harm language), and it verifies that the top pick fits the inferred profile before answering. Every step is saved: full traces for four queries are in [docs/ai_interactions.md](docs/ai_interactions.md), and raw traces from every run go to `logs/agent_traces.jsonl`.

**3. Test Harness.** `python -m src.evaluate` runs 20 predefined checks five times each and prints a pass/fail table with confidence and consistency, saved to [docs/evaluation_results.md](docs/evaluation_results.md).

I did not attempt the fine-tuning/specialization stretch: without an LLM it would only be a style tweak to template text, which wouldn't be a meaningful claim.

## Design Decisions and Trade-offs

- **Offline TF-IDF retrieval instead of an LLM API.** Anyone can clone and run it with no keys or cost, and the results are deterministic and testable (the harness checks identical output across 5 runs). The trade-off is that it only matches *words*: no semantic understanding and no synonyms I didn't write into the knowledge base. Negation is handled by a small rule-based parser, which covers common phrasings only.
- **Retrieval builds the profile; the original scorer ranks.** I kept VibeFinder 1.0's explainable scoring rather than replacing it, so retrieval genuinely changes behavior while every score stays auditable. The trade-off is that it inherits 1.0's known genre-over-mood bias.
- **Refuse over guess.** Below the 0.15 confidence threshold the system declines. This costs some coverage but avoids confident nonsense.
- **Safety check before retrieval.** A self-harm query should never get a playlist, so this check runs before everything else. A keyword list is crude, but it fails safe.
- **Small hand-built knowledge base (37 entries).** It's easy to audit and tune, but coverage is limited to what I wrote.

## Testing Summary

Full table: [docs/evaluation_results.md](docs/evaluation_results.md).

**Results: 19/19 pytest tests pass. 20/20 evaluation checks pass. All 20 are deterministic across 5 repeated runs. Mean confidence on in-scope queries is 0.49.** The checks cover 7 in-scope queries, 3 negation queries, 1 multi-genre query, 3 agent queries, 4 invalid-input cases, 1 self-harm case and 1 gibberish case.

**What worked:** Guardrails handled every bad input without a crash. Retrieval put the right entries first for situation words like "workout", "study" and "sleep".

**What didn't (at first):** The first version passed all 13 planned checks, yet manual probing found real failures:
- **Negation was ignored.** "not sad please, something happy" returned sad songs, and "anything but jazz" returned jazz.
- **Mixed requests collapsed.** "reggae and metal mixed" returned only reggae.
- **Word forms didn't match.** "I want to relax" found nothing because the knowledge base says "relaxed".

I fixed all three: a query parser (`src/query_parser.py`) separates what the user wants from what they want to avoid, the profile now keeps several genres and moods, and a light stemmer matches word forms. Each fix has pytest tests and evaluation cases that failed before the change.

**Still open:** Incidental words add noise (the word "night" pulled in a synthwave entry for a study query). Negation is rule-based, so unusual phrasing like "I'm sick of jazz" is not caught. Matching is still word-based, with no semantic understanding.

**What I learned:** A passing test suite is a floor, not proof. Adversarial probing found more real problems in 5 minutes than the 13 planned cases did, and the safety gap (self-harm wording originally got a generic "couldn't match" reply) only showed up that way.

## Reflection

The most useful lesson was how much of "AI quality" is plumbing around the model: input validation, confidence thresholds, refusal paths, logging and repeatable evaluation. Making retrieval *drive* the output, instead of printing alongside it, also made the system far easier to debug, because every recommendation traces back to named sources. My honest responsible-AI reflection (limitations, misuse, surprises, and how I worked with AI) is in [docs/model_card.md](docs/model_card.md).

## Project Structure

```
src/        recommender.py (scoring), agent.py, query_parser.py, retriever.py, guardrails.py, rag.py, evaluate.py, main.py
tests/      test_recommender.py, test_rag.py, test_agent.py
data/       songs.csv, knowledge_base.json, song_notes.json
diagrams/   architecture.mmd
docs/       model_card.md, evaluation_results.md, ai_interactions.md, vibefinder_1_0_readme.md
logs/       vibefinder.log (git-ignored)
assets/     images for the README
```
