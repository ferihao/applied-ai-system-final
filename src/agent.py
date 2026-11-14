"""Agentic wrapper: plan -> act (tool calls) -> check -> recover or ask.

Tools the agent can call:
  recommend(query)              the RAG pipeline (src/rag.py)
  correct_spelling(query)       replace unknown words with their closest knowledge-base word
  suggest_options()             build a clarifying question from known situations
Every step is recorded in a trace (also appended to logs/agent_traces.jsonl).
"""
import difflib
import json
import os
import re
from typing import Dict, List

from src.rag import VibeFinder
from src.retriever import stem

TRACE_PATH = "logs/agent_traces.jsonl"
KEEP_ALWAYS = {"not", "no", "without", "except", "avoid", "never", "hate", "dont", "don't", "anything",
               "everything", "but", "other", "than"}
MAX_ACTIONS = 3


class VibeAgent:
    def __init__(self, finder: VibeFinder = None):
        self.finder = finder or VibeFinder()

    # ---- tools -------------------------------------------------------------
    def correct_spelling(self, query: str) -> str:
        """Fixes likely typos by matching unknown words to the closest known vocabulary word."""
        vocab = list(self.finder.retriever.idf) if self.finder.retriever else []
        out = []
        for word in re.findall(r"[A-Za-z0-9\-']+", query):
            low = word.lower()
            if stem(low) in vocab or low in KEEP_ALWAYS or not vocab:
                out.append(word)
                continue
            close = difflib.get_close_matches(stem(low), vocab, n=1, cutoff=0.75)
            out.append(close[0] if close else word)
        return " ".join(out)

    def suggest_options(self) -> str:
        entries = self.finder.retriever.entries if self.finder.retriever else []
        names = [e["title"].split(": ", 1)[1] for e in entries if e["id"].startswith("activity-")][:5]
        return ("I couldn't tell what you're in the mood for. Are you looking for music for something like: "
                + ", ".join(names) + "? Or name a genre or mood.")

    # ---- loop --------------------------------------------------------------
    def run(self, query) -> Dict:
        trace: List[Dict] = []

        def log(step, thought, tool=None, tool_input=None, observation=None):
            trace.append({"step": len(trace) + 1, "phase": step, "thought": thought, "tool": tool,
                          "input": tool_input, "observation": observation})

        log("plan", "1) recommend via RAG  2) check status and confidence  3) if low confidence, correct likely typos "
                    "and retry once  4) if still unclear, ask a clarifying question  "
                    "5) verify the top result matches the inferred profile before answering")
        result = self.finder.recommend(query)
        log("act", "Run the RAG pipeline on the raw query.", "recommend", query,
            f"status={result['status']} confidence={result['confidence']}")

        if result["status"] in ("invalid", "safety"):
            log("check", f"Guardrail status '{result['status']}': stop. The agent must not retry around a guardrail.")
            return self._finish(result, trace)

        actions = 1
        if result["status"] == "low_confidence" and isinstance(query, str):
            rewritten = self.correct_spelling(query)
            log("check", "Low confidence: some words may be typos of words the knowledge base knows. "
                         "Try spelling correction.", "correct_spelling", query, repr(rewritten))
            if rewritten and rewritten.lower() != query.lower() and actions < MAX_ACTIONS:
                result = self.finder.recommend(rewritten)
                actions += 1
                log("act", "Retry with the rewritten query.", "recommend", rewritten,
                    f"status={result['status']} confidence={result['confidence']}")
            else:
                log("check", "Spelling correction changed nothing, so retrying would give the same result.")

        if result["status"] == "low_confidence":
            question = self.suggest_options()
            log("act", "Still unclear. Ask the user instead of guessing.", "suggest_options", None, question)
            return self._finish({"status": "needs_clarification", "confidence": result["confidence"],
                                 "message": question, "recommendations": []}, trace)

        # verification: does the answer actually fit the profile we inferred?
        if result["status"] == "ok":
            profile, recs = result["profile"], result["recommendations"]
            top = next((s for s in self.finder.songs if recs and s["title"] == recs[0]["title"]), None)
            if top is None:
                log("check", "No recommendations survived filtering.")
                result["verified"] = False
            else:
                fits = (top["genre"] in profile.get("genres", []) or top["mood"] in profile.get("moods", [])
                        or abs(top["energy"] - profile["energy"]) <= 0.3)
                result["verified"] = fits
                log("check", f"Top pick '{top['title']}' ({top['genre']}/{top['mood']}, energy {top['energy']}) vs "
                             f"profile (energy {profile['energy']}): {'consistent' if fits else 'MISMATCH, flagging'}.")
        return self._finish(result, trace)

    def _finish(self, result: Dict, trace: List[Dict]) -> Dict:
        result["trace"] = trace
        try:
            os.makedirs(os.path.dirname(TRACE_PATH), exist_ok=True)
            with open(TRACE_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"status": result["status"], "trace": trace}) + "\n")
        except OSError:
            pass
        return result


SAMPLE_QUERIES = [
    "anything but jazz, I want to relax",
    "heavey metl workot",
    "tunes for jogging",
    "self harm",
]
BEGIN, END = "<!-- AGENT-TRACES:BEGIN -->", "<!-- AGENT-TRACES:END -->"


def format_trace(query: str, result: Dict) -> str:
    lines = [f"### Query: `{query}`", "", f"Final status: **{result['status']}**"
             + (f", top picks: {', '.join(r['title'] for r in result['recommendations'][:3])}" if result["recommendations"] else ""),
             ""]
    for t in result["trace"]:
        tool = f" -> `{t['tool']}({t['input']!r})`" if t["tool"] else ""
        obs = f"  \n   observed: {t['observation']}" if t["observation"] else ""
        lines.append(f"{t['step']}. **{t['phase']}**{tool}: {t['thought']}{obs}")
    return "\n".join(lines) + "\n"


def save_traces(path: str = "docs/ai_interactions.md") -> None:
    """Runs the sample queries and rewrites the traces section of docs/ai_interactions.md."""
    agent = VibeAgent()
    body = "\n".join(format_trace(q, agent.run(q)) for q in SAMPLE_QUERIES)
    section = (f"{BEGIN}\n## VibeAgent Reasoning Traces (Capstone Agentic Workflow)\n\n"
               "Generated by `python -m src.agent --save-traces`. Each trace shows the plan, every tool call, and the "
               "checks the agent ran. Raw traces from every run are also appended to `logs/agent_traces.jsonl` "
               "(git-ignored).\n\n" + body + f"\n{END}\n")
    text = open(path, encoding="utf-8").read()
    if BEGIN in text:
        text = text[:text.index(BEGIN)] + section + text[text.index(END) + len(END) + 1:]
    else:
        text = text.rstrip() + "\n\n---\n\n" + section
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    import sys
    if "--save-traces" in sys.argv:
        save_traces()
        print("Traces written to docs/ai_interactions.md")
