# Presentation Outline (5-7 minutes)

Run `source .venv/bin/activate` first and keep a terminal open in the project folder.

| Time | Section | What to say / show |
|---|---|---|
| 0:00-0:45 | **Problem and origin** | "My Module 3 recommender made users fill in rigid fields: genre, mood, energy, acoustic. I turned it into a system that takes plain English and explains its picks." Show the one-line architecture: query, retrieval, profile, scoring, verification. |
| 0:45-1:45 | **Architecture** | Show `diagrams/architecture.mmd` rendered. Name the parts: guardrails, retriever (two sources), profile builder, scorer, agent loop, evaluator, and where a human reviews. Key point: retrieved text builds the profile, so changing the knowledge base changes the answer. |
| 1:45-3:30 | **Live demo (3 commands)** | 1. `python -m src.main "high energy workout"` shows retrieved sources and cited reasons. 2. `python -m src.main "anything but jazz, I want to relax"` shows negation. 3. `python -m src.main "heavey metl workot"` shows the agent's tool calls: refused, corrected the spelling, retried, answered. |
| 3:30-4:30 | **Guardrails** | Run `python -m src.main "I want to kill myself"` (support resources, no songs) and `python -m src.main "tunes for jogging"` (asks a clarifying question instead of guessing). Say: the agent never retries around a guardrail. |
| 4:15-4:30 | **LLM step (optional)** | `python -m src.main "sad rainy heartbreak" --llm` shows Ollama writing grounded explanations next to the numeric scores. |
| 4:30-5:30 | **Reliability** | Run `python -m src.evaluate`. 20/20 pass and every result is identical across 5 runs. Then the honest part: "My first 13 checks all passed, but probing found negation, multi-genre, and typo failures. I fixed them and added tests." |
| 5:30-6:30 | **Limits and learning** | Matching is word-based, not semantic. Negation parsing is rule-based. The LLM step is optional and its wording varies between runs. The crisis check is an English keyword list. Lesson: a passing test suite is a floor, not proof. |
| 6:30-7:00 | **Close** | GitHub link, README, `docs/model_card.md`. |

## Vocabulary to use aloud
agent, guardrail, human-in-the-loop, orchestration, RAG, reliability testing, verification.

## Likely questions
- **"Is this really RAG?"** Yes, in `--llm` mode: retrieved entries drive the profile, and a local Ollama model writes the explanation from only that retrieved context. The default mode uses templates for reproducibility.
- **"Why is the LLM optional?"** The default mode is offline, free, deterministic and testable. The LLM mode is free and local, but its wording varies between runs, so it is not used for evaluation. It never ranks songs.
- **"What would you fix next?"** Semantic retrieval (embeddings), a larger catalog, and a real crisis classifier.
