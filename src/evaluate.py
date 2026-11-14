"""Reliability harness: runs fixed queries and reports accuracy, confidence and consistency.

Usage: python -m src.evaluate   (writes docs/evaluation_results.md)
"""
from statistics import mean

from src.rag import VibeFinder

# (query, expected status, acceptable genres or moods for the TOP result; empty = n/a)
CASES = [
    ("chill music for studying late at night", "ok", {"lofi", "ambient", "classical", "chill", "focused", "peaceful"}),
    ("high energy workout", "ok", {"rock", "metal", "electronic", "hip-hop", "intense", "energetic", "angry"}),
    ("sad rainy heartbreak", "ok", {"blues", "folk", "sad", "melancholy"}),
    ("something to fall asleep to", "ok", {"ambient", "classical", "peaceful", "relaxed"}),
    ("upbeat party with friends", "ok", {"pop", "electronic", "hip-hop", "happy", "energetic"}),
    ("jazz for cooking dinner", "ok", {"jazz", "reggae", "folk", "relaxed", "happy"}),
    ("road trip", "ok", {"rock", "synthwave", "country", "happy", "energetic"}),
    ("", "invalid", set()),
    ("   ", "invalid", set()),
    ("12345 !!!", "invalid", set()),
    ("x" * 400, "invalid", set()),
    ("I want to kill myself music", "safety", set()),
    ("asdfgh qwerty zxcv", "low_confidence", set()),
]
REPEATS = 5


def evaluate():
    vf = VibeFinder()
    rows, confidences = [], []
    for query, expected, accept in CASES:
        runs = [vf.recommend(query, k=3) for _ in range(REPEATS)]
        first = runs[0]
        consistent = all([r["title"] for r in x["recommendations"]] == [r["title"] for r in first["recommendations"]] for x in runs)
        passed = first["status"] == expected
        detail = first["status"]
        if passed and expected == "ok":
            top = next(s for s in vf.songs if s["title"] == first["recommendations"][0]["title"])
            passed = top["genre"] in accept or top["mood"] in accept
            detail = f"top={top['title']} ({top['genre']}/{top['mood']})"
            confidences.append(first["confidence"])
        rows.append((query[:40] or "(empty)", detail, first["confidence"], consistent, passed))
    return rows, confidences


def main() -> None:
    rows, confs = evaluate()
    lines = ["| Test Input | Result | Confidence | Consistent x5 | Pass |", "|---|---|---|---|---|"]
    lines += [f"| {q!r} | {d} | {c} | {'yes' if cons else 'no'} | {'Pass' if p else 'FAIL'} |" for q, d, c, cons, p in rows]
    passed = sum(r[4] for r in rows)
    summary = (f"\n**{passed}/{len(rows)} checks passed; {sum(r[3] for r in rows)}/{len(rows)} deterministic across "
               f"{REPEATS} runs; mean confidence on in-scope queries {mean(confs):.2f}.**\n")
    out = "# Evaluation Results\n\n" + "\n".join(lines) + "\n" + summary
    print(out)
    with open("docs/evaluation_results.md", "w", encoding="utf-8") as f:
        f.write(out)


if __name__ == "__main__":
    main()
