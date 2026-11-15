# Portfolio Entry: VibeFinder RAG

**Code:** https://github.com/ferihao/applied-ai-system-final

**What it is:** A retrieval-augmented, agent-driven music recommender that turns free-text requests into explained, verified playlists. It runs offline by default, and an optional free local Ollama model can write the explanations. It grew out of my Module 3 Music Recommender Simulation (VibeFinder 1.0).

**What this project says about me as an AI engineer**

I treat an AI system as more than a model call: the checking around it matters as much as the output. In this project I built retrieval that actually drives the result, then spent as much effort on guardrails, confidence thresholds, a safety check for self-harm language, an evaluation harness, and a model card that states what the system gets wrong. I trust tests only as far as they were written: my first 13 planned checks all passed, and manual probing still found negation, multi-genre and typo failures that I then fixed and covered with tests. I also scope honestly. I made the default mode deterministic and offline so every claim is reproducible, and added the LLM generation step as an optional local Ollama mode behind a grounding guardrail, because it is not deterministic and I won't claim otherwise. I'd bring the same habits to production work: make the AI's behavior traceable, test where it is likely to fail, and be clear about its limits.

**Highlights:** TF-IDF retrieval over two sources · negation and multi-genre handling · plan-act-check agent with saved reasoning traces · 19 unit tests and 20 evaluation checks run five times each · responsible-AI model card.
