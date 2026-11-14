"""Splits a query into what the user wants and what they want to avoid."""
import re
from typing import Tuple

# A negator opens a scope that runs to the next punctuation/conjunction (max 3 words).
NEGATORS = {"not", "no", "without", "except", "avoid", "never", "hate", "dont", "don't", "nothing"}
PHRASE_NEGATORS = ("anything but", "everything but", "other than", "anything except")
SCOPE_END = {"and", "or", "but", "please", "so", "because"}
MAX_SCOPE = 3


def parse_query(query: str) -> Tuple[str, str]:
    """Returns (positive_text, negative_text)."""
    q = query.lower()
    for phrase in PHRASE_NEGATORS:
        q = q.replace(phrase, "not")
    positive, negative = [], []
    scope = 0
    for token in re.findall(r"[a-z0-9\-']+|[,.;!?]", q):
        if token in ",.;!?":
            scope = 0
        elif token in NEGATORS:
            scope = MAX_SCOPE
        elif scope and token in SCOPE_END:
            scope = 0
            positive.append(token)
        elif scope:
            negative.append(token)
            scope -= 1
        else:
            positive.append(token)
    return " ".join(positive), " ".join(negative)
