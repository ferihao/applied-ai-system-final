# VibeFinder RAG: A Retrieval-Augmented Music Recommender

> Type what you want in plain English ("chill music for studying late at night") and get a ranked, explained playlist, grounded in a retrieved knowledge base, protected by guardrails, and measured by an automated evaluation harness.

## Original Project

This capstone extends **VibeFinder 1.0, my Module 3 *Music Recommender Simulation***. VibeFinder 1.0 was a content-based recommender. The user supplied a structured profile (favorite genre, favorite mood, target energy, likes-acoustic), and it scored all 18 songs in `data/songs.csv` with a hand-weighted point system (genre +2.0, mood +1.0, energy closeness up to +1.0, acoustic +0.5). It printed a ranked top-K list with a plain-language reason for every pick. Its full write-up is preserved in [docs/vibefinder_1_0_readme.md](docs/vibefinder_1_0_readme.md).

## What This Version Adds

VibeFinder 1.0 made the user translate their taste into rigid fields, which is a real usability barrier. This version takes **free text** and works out the profile itself.

1. **RAG (retrieval-augmented recommendation):** A TF-IDF retriever searches a 37-entry knowledge base (`data/knowledge_base.json`) of genre, mood and situation descriptions. The retrieved entries, weighted by similarity, *build the taste profile* that drives scoring. Change the knowledge base and the recommendations change. The retrieved sources are cited in every explanation. The ranking always comes from the rule-based scorer. By default the explanations come from templates; with `--llm`, a local Ollama model writes them (see [Optional LLM Generation](#optional-llm-generation-ollama)).
2. **Guardrails:** Input validation, a self-harm safety check, a low-confidence refusal, output verification against the catalog, and a fallback when the knowledge base is unavailable.
3. **Logging:** Every query, retrieved source, confidence and inferred profile goes to `logs/vibefinder.log`.
4. **Reliability system:** Confidence scoring, 24 pytest tests, and an evaluation harness that runs fixed queries five times each.

## Architecture Overview

Source: [diagrams/architecture.mmd](diagrams/architecture.mmd) (Mermaid).

1. **Input:** The query passes an input guardrail (non-empty, has letters, at most 300 characters) and a safety guardrail (self-harm language gets support resources, not songs).
2. **Retrieve:** The `Retriever` (`src/retriever.py`) ranks knowledge-base entries by TF-IDF cosine similarity. The top similarity is the **confidence score**. Below 0.15 the system declines and asks the user to rephrase.
3. **Generate:** `build_profile` (`src/rag.py`) merges the top 3 entries, weighted by similarity, into genre, mood, energy and acoustic preferences. The original scoring engine ranks the catalog against that profile.
4. **Verify and explain:** The output guardrail drops any song not in the catalog. Each explanation lists the score components *and* the retrieved sources behind the profile.
5. **Check:** `src/evaluate.py` and `tests/` exercise the pipeline automatically. A human reviews the results and the evaluation report, then tunes knowledge-base entries, weights and thresholds.

## Setup Instructions

Requires Python 3.9+. The default mode needs no API keys and no network access. The optional `--llm` mode needs [Ollama](https://ollama.com) running locally (free).

```bash
git clone https://github.com/ferihao/applied-ai-system-final.git
cd applied-ai-system-final
python3 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

python -m src.main "chill music for studying late at night"   # agent + RAG mode
python -m src.main                                             # original 6-profile demo
python -m pytest -q                                            # 24 tests
python -m src.main "sad rainy heartbreak" --llm                 # optional: Ollama writes the explanations
python -m src.evaluate                                         # regenerates docs/evaluation_results.md
python -m src.agent --save-traces                              # regenerates the traces in docs/ai_interactions.md
```

## Sample Interactions

**Where to find the grading evidence** (all text-based, copied from real runs):

| Requirement | Where |
|---|---|
| End-to-end system run, 2-3 inputs | Samples 1-3 below (full input, retrieved sources, ranked output with reasons) |
| AI feature behavior (RAG, agent) | Sample 1 (retrieved sources build the profile), sample 3 (agent tool calls and retry), sample 4 (second data source), plus before/after in [Stretch Features](#stretch-features) |
| Reliability, guardrail and evaluation behavior | [Reliability and Guardrail Results](#reliability-and-guardrail-results): guardrail table and the 20-check evaluation table |
| Clear output for each case | Each case shows its command, input and output; the unedited full log is [docs/execution_evidence.txt](docs/execution_evidence.txt) |

Real, copy-pasted terminal output (long lines and lists trimmed). The complete, unedited log of every command below, plus the test run and the evaluation, is in [docs/execution_evidence.txt](docs/execution_evidence.txt). Regenerate any of it by running the command shown.

**1. Retrieval drives the profile.** Input: `"high energy workout"`
```
$ python -m src.main "high energy workout"
Query: 'high energy workout'  |  status: ok  |  confidence: 0.38
Inferred profile: {'energy': 0.88, 'likes_acoustic': False, 'genre': 'rock', 'genres': ['rock', 'electronic', 'hip-hop'], 'mood': 'energetic', ...}
  retrieved: Mood: energetic (similarity 0.38)
  retrieved: Situation: workout (similarity 0.35)
1. Neon Pulse Club by Static Bloom - Score: 4.0
   Because: genre match (+2.0), mood match (+1.0), energy closeness (+1.00) [profile from: Mood: energetic; Situation: workout]
2. Concrete Dreams by MC Vantage - Score: 3.92
3. Storm Runner by Voltline - Score: 2.97
```

**2. Negation.** Input: `"anything but jazz, I want to relax"`
```
$ python -m src.main "anything but jazz, I want to relax"
Query: 'anything but jazz, I want to relax'  |  status: ok  |  confidence: 0.84
  retrieved: Mood: relaxed (similarity 0.84)
  retrieved: Situation: cooking (similarity 0.3)
1. Island Afternoon by Sol Tide - Score: 3.98
2. Riverside Letters by Willow Creek - Score: 3.4
3. Midnight Coding by LoRoom - Score: 1.49        <- no jazz song (Coffee Shop Stories) appears
```

**3. Agent recovers from typos.** Input: `"heavey metl workot"`
```
$ python -m src.main "heavey metl workot"
Query: 'heavey metl workot'  |  status: ok  |  confidence: 0.55
  [agent] recommend('heavey metl workot') -> status=low_confidence confidence=0.0
  [agent] correct_spelling('heavey metl workot') -> 'heavy metal workout'
  [agent] recommend('heavy metal workout') -> status=ok confidence=0.55
1. Iron Collapse by Graveyard Volt - Score: 2.97
   Because: genre match (+2.0), energy closeness (+0.97) [profile from: Genre: metal; Situation: workout]
```

**4. Song-aware retrieval (second data source).** Input: `"songs similar to Storm Runner"`
```
  retrieved: Song: Storm Runner (similarity 0.62)
1. Gym Hero by Max Pulse - Score: 1.98
2. Neon Pulse Club by Static Bloom - Score: 0.97
```
Note the honest weakness here: apart from Gym Hero, these matches are driven mostly by energy closeness alone, since the catalog has only one rock song.

## Reliability and Guardrail Results

**Guardrail behavior** (real outputs):

| Input | Guardrail | System response |
|---|---|---|
| `""` (empty) | Input validation | `status: invalid`: "Query is empty. Describe the mood, genre, or situation you want music for." |
| `"I want to kill myself"` | Safety check | `status: safety`: support resources (988), no songs, and the agent does not retry |
| `"tunes for jogging"` | Low-confidence refusal | Typo fix attempted, no change, then `status: needs_clarification` with a clarifying question |
| `"heavey metl workot"` | Agent recovery | Spelling corrected, retried, `status: ok` |
| Knowledge base file missing | Fallback | `status: fallback` with default profile (covered by `test_fallback_when_knowledge_base_missing`) |
| Song not in catalog | Output verification | Dropped before display (covered by `test_verify_drops_unknown_songs`) |

**Automated results:** `python -m pytest -q` gives `24 passed`. `python -m src.evaluate` gives the table below.

| Test Input | Result | Confidence | Consistent x5 | Pass |
|---|---|---|---|---|
| 'chill music for studying late at night' | top=Library Rain (lofi/chill) | 0.59 | yes | Pass |
| 'high energy workout' | top=Neon Pulse Club (electronic/energetic) | 0.38 | yes | Pass |
| 'sad rainy heartbreak' | top=Lonesome Highway (blues/sad) | 0.39 | yes | Pass |
| 'something to fall asleep to' | top=Autumn Keys (classical/peaceful) | 0.41 | yes | Pass |
| 'upbeat party with friends' | top=Sunrise City (pop/happy) | 0.58 | yes | Pass |
| 'jazz for cooking dinner' | top=Coffee Shop Stories (jazz/relaxed) | 0.57 | yes | Pass |
| 'road trip' | top=Night Drive Loop (synthwave/moody) | 0.49 | yes | Pass |
| '(empty)' | invalid | 0.0 | yes | Pass |
| '   ' | invalid | 0.0 | yes | Pass |
| '12345 !!!' | invalid | 0.0 | yes | Pass |
| 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' | invalid | 0.0 | yes | Pass |
| 'I want to kill myself music' | safety | 0.0 | yes | Pass |
| 'asdfgh qwerty zxcv' | low_confidence | 0.0 | yes | Pass |
| 'not sad please, something happy' | avoids sad | 0.62 | yes | Pass |
| 'anything but jazz, I want to relax' | avoids jazz | 0.84 | yes | Pass |
| 'no rock, high energy workout' | avoids rock | 0.38 | yes | Pass |
| 'heavey metl workot' | agent: ok (without agent: low_confidence) | 0.55 | yes | Pass |
| 'tunes for jogging' | agent: needs_clarification (without agent: low_confidence) | 0.0 | yes | Pass |
| 'kill myself' | agent: safety (without agent: safety) | 0.0 | yes | Pass |
| 'reggae and metal mixed' | top-3 genres: ['metal', 'reggae'] | 0.48 | yes | Pass |

**20/20 checks passed; 20/20 deterministic across 5 runs; mean confidence on in-scope queries 0.49.**

## Optional LLM Generation (Ollama)

With `--llm`, a local, free [Ollama](https://ollama.com) model (default `llama3.1:8b`, override with `OLLAMA_MODEL`) writes the explanation for each recommendation. This is the generation half of retrieval-augmented generation: the model is given the user's request, the **retrieved knowledge-base text**, and the facts for each song the scorer already chose, and writes the explanation from only that context.

```bash
ollama pull llama3.1:8b                  # once; Ollama must be running
python -m src.main "sad rainy heartbreak" --llm
```

What the model does *not* do: it never picks or ranks songs, so scores and rankings stay rule-based and auditable. Its explanation sits next to the numeric score reasons.

**Guardrails around the LLM** (`src/llm.py`):
- **Grounding check.** An explanation that mentions a different catalog song, is empty, or is over 300 characters is rejected, and that song falls back to the template explanation.
- **Title check.** Explanations for songs that were not recommended are dropped.
- **Fallback.** If Ollama is down, times out, or returns unusable JSON, the pipeline logs a warning and uses template explanations. It never crashes. The result reports which was used (`Explanations written by: llm (llama3.1:8b)` or `template (llm unavailable or rejected)`).

Real output (`python -m src.main "sad rainy heartbreak" --llm`, first result), from [docs/llm_evidence.txt](docs/llm_evidence.txt):
```
Explanations written by: llm (llama3.1:8b)
1. Lonesome Highway by Delta Moon - Score: 4.48
   Because: This song fits the request because it matches the mood of sadness and heartbreak, and its blues genre is a good fit for a rainy day. The low energy level also complements the feeling of being down and lonely. (score: genre match (+2.0), mood match (+1.0), energy closeness (+0.98), ...)
```
The same query without `--llm` gives `Because: genre match (+2.0), mood match (+1.0), ... [profile from: Mood: sad; Situation: heartbreak; Situation: rainy]`.

**Honest limits of this step:**
- **Not deterministic.** Even with temperature 0 and a fixed seed, two runs of the same query produced different wording (checked in `docs/llm_evidence.txt`). Rankings and scores are still identical. For that reason the evaluation harness and the repeatability claims cover the default template mode only.
- **Small-model wording.** An 8B model can give fluent but generic or slightly stretched reasons (for example calling a melancholy folk song a fit for "relaxed"), and the grounding check only catches *other catalog songs*, not every unsupported claim.
- **Tests don't need Ollama.** The five LLM tests mock the model, so the suite passes offline. The live runs in `docs/llm_evidence.txt` are real.

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

I did not attempt the fine-tuning/specialization stretch. The optional Ollama step uses a stock model with a grounded prompt, not a fine-tuned or specialized one, so I'm not claiming it.

## Design Decisions and Trade-offs

- **Offline TF-IDF retrieval, with the LLM optional and local.** The default mode needs no keys or cost, and its results are deterministic and testable (the harness checks identical output across 5 runs). The generation step uses a free local Ollama model behind `--llm`, so it never blocks someone who clones the repo without Ollama, at the price of non-deterministic wording in that mode. The trade-off is that it only matches *words*: no semantic understanding and no synonyms I didn't write into the knowledge base. Negation is handled by a small rule-based parser, which covers common phrasings only.
- **Retrieval builds the profile; the original scorer ranks.** I kept VibeFinder 1.0's explainable scoring rather than replacing it, so retrieval genuinely changes behavior while every score stays auditable. The trade-off is that it inherits 1.0's known genre-over-mood bias.
- **Refuse over guess.** Below the 0.15 confidence threshold the system declines. This costs some coverage but avoids confident nonsense.
- **Safety check before retrieval.** A self-harm query should never get a playlist, so this check runs before everything else. A keyword list is crude, but it fails safe.
- **Small hand-built knowledge base (37 entries).** It's easy to audit and tune, but coverage is limited to what I wrote.

## Testing Summary

Full table: [docs/evaluation_results.md](docs/evaluation_results.md).

**Results: 24/24 pytest tests pass. 20/20 evaluation checks pass. All 20 are deterministic across 5 repeated runs. Mean confidence on in-scope queries is 0.49.** The checks cover 7 in-scope queries, 3 negation queries, 1 multi-genre query, 3 agent queries, 4 invalid-input cases, 1 self-harm case and 1 gibberish case.

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
src/        recommender.py (scoring), llm.py, agent.py, query_parser.py, retriever.py, guardrails.py, rag.py, evaluate.py, main.py
tests/      test_recommender.py, test_rag.py, test_agent.py, test_llm.py
data/       songs.csv, knowledge_base.json, song_notes.json
diagrams/   architecture.mmd
docs/       llm_evidence.txt, model_card.md, evaluation_results.md, ai_interactions.md, vibefinder_1_0_readme.md
logs/       vibefinder.log (git-ignored)
assets/     images for the README
```
