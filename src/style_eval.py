"""Measures how much the few-shot 'concise' specialization changes LLM output vs the default prompt.

Usage: python -m src.style_eval   (needs Ollama; writes docs/style_comparison.md)
Rules checked per explanation: one sentence, at most 18 words, states low/medium/high energy,
no filler phrases.
"""
import re
from statistics import mean

from src.llm import OLLAMA_MODEL
from src.rag import VibeFinder

QUERIES = ["chill music for studying late at night", "high energy workout", "sad rainy heartbreak",
           "upbeat party with friends", "something to fall asleep to"]
FILLER = ("this song", "fits the request", "this track")


def llm_text(explanation: str) -> str:
    return explanation.split(" (score:")[0]


def check(text: str) -> dict:
    words = len(text.split())
    sentences = len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s])
    low = text.lower()
    return {"one_sentence": sentences == 1, "max_18_words": words <= 18, "words": words,
            "states_energy": bool(re.search(r"\b(low|medium|high) energy\b", low)),
            "no_filler": not any(f in low for f in FILLER)}


def run(style: str):
    vf = VibeFinder(use_llm=True, llm_style=style)
    rows = []
    for q in QUERIES:
        r = vf.recommend(q, k=3)
        for rec in r["recommendations"]:
            if rec.get("explanation_source") == "llm":
                rows.append(check(llm_text(rec["explanation"])))
    return rows


def main() -> None:
    results = {s: run(s) for s in ("default", "concise")}
    lines = [f"# Style Comparison: default prompt vs few-shot 'concise' specialization\n",
             f"Model: `{OLLAMA_MODEL}`, temperature 0, seed 7. {len(QUERIES)} queries x top 3 songs. "
             "Only explanations actually written by the LLM and accepted by the grounding guardrail are counted.\n",
             "| Metric | default | concise |", "|---|---|---|"]
    def pct(rows, key):
        return f"{100 * sum(r[key] for r in rows) / len(rows):.0f}%" if rows else "n/a"
    lines.append("| Explanations measured | " + " | ".join(str(len(results[s])) for s in results) + " |")
    lines.append("| Average words | " + " | ".join(f"{mean(r['words'] for r in results[s]):.1f}" if results[s] else "n/a" for s in results) + " |")
    for key, label in (("one_sentence", "Exactly one sentence"), ("max_18_words", "At most 18 words"),
                       ("states_energy", "States low/medium/high energy"), ("no_filler", "No filler phrases")):
        lines.append(f"| {label} | " + " | ".join(pct(results[s], key) for s in results) + " |")
    out = "\n".join(lines) + "\n"
    print(out)
    with open("docs/style_comparison.md", "w", encoding="utf-8") as f:
        f.write(out)


if __name__ == "__main__":
    main()
