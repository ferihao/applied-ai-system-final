"""Pure-Python TF-IDF retriever over the genre/mood/situation knowledge base."""
import json
import math
import re
from collections import Counter
from typing import Dict, List, Tuple

STOPWORDS = {"a", "an", "the", "for", "to", "of", "and", "or", "i", "me", "my", "some",
             "music", "songs", "song", "want", "need", "like", "something", "play", "give",
             "with", "in", "on", "is", "it", "that", "this", "when", "while", "of"}


def stem(token: str) -> str:
    """Very light suffix stripping so 'relax', 'relaxed' and 'relaxing' match."""
    for suffix in ("ing", "ed", "es", "s", "e"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> List[str]:
    return [stem(t) for t in re.findall(r"[a-z0-9\-]+", text.lower()) if t not in STOPWORDS]


def load_knowledge_base(path: str) -> List[Dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Retriever:
    """Ranks knowledge-base entries against a free-text query by TF-IDF cosine similarity."""

    def __init__(self, entries: List[Dict]):
        self.entries = entries
        self.docs = [Counter(tokenize(f"{e['title']} {e['text']}")) for e in entries]
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vectors = [self._vec(d) for d in self.docs]

    def _vec(self, counts: Counter) -> Dict[str, float]:
        vec = {t: c * self.idf[t] for t, c in counts.items() if t in self.idf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def search(self, query: str, top_n: int = 3) -> List[Tuple[Dict, float]]:
        q = self._vec(Counter(tokenize(query)))
        scored = [(e, sum(w * v.get(t, 0.0) for t, w in q.items()))
                  for e, v in zip(self.entries, self.vectors)]
        scored = [(e, s) for e, s in scored if s > 0]
        scored.sort(key=lambda p: p[1], reverse=True)
        return scored[:top_n]
