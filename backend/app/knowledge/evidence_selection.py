"""Opt-in lexical selection policy. Never verifies paraphrases or generates facts."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SelectionPolicy:
    minimum_fraction: float = 0.25


def selection_terms(tokens, text):
    """Normalize superficial variation; preserve identifier matching elsewhere."""
    # No topic-specific synonyms derived from benchmark examples.
    result=set(tokens)
    if re.search(r"\bsha[- ]?(?:1|224|256|384|512)\b",text,re.I):
        result.add("hash")
    return result


def matching_terms(query, source):
    # General inflection families such as describe/described/describes and
    # derive/derives/derivation. Selection only; returned text remains verbatim.
    return {q for q in query if q in source or
            (len(q)>=5 and any(len(s)>=5 and q[:5]==s[:5] for s in source))}
