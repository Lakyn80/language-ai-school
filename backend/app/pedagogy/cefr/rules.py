from dataclasses import dataclass
from .levels import CEFRLevel


@dataclass
class CEFRRules:
    allowed_tenses: list[str]
    max_sentence_words: int
    allow_passive: bool
    allow_conditionals: bool
    allow_subordinate_clauses: bool


CEFR_RULES = {
    CEFRLevel.A1: CEFRRules(
        allowed_tenses=["present_simple"],
        max_sentence_words=8,
        allow_passive=False,
        allow_conditionals=False,
        allow_subordinate_clauses=False,
    ),
    CEFRLevel.A2: CEFRRules(
        allowed_tenses=["present_simple", "past_simple"],
        max_sentence_words=12,
        allow_passive=False,
        allow_conditionals=False,
        allow_subordinate_clauses=True,
    ),
    CEFRLevel.B1: CEFRRules(
        allowed_tenses=["present", "past", "future"],
        max_sentence_words=18,
        allow_passive=True,
        allow_conditionals=False,
        allow_subordinate_clauses=True,
    ),
    CEFRLevel.B2: CEFRRules(
        allowed_tenses=["all_basic"],
        max_sentence_words=25,
        allow_passive=True,
        allow_conditionals=True,
        allow_subordinate_clauses=True,
    ),
    CEFRLevel.C1: CEFRRules(
        allowed_tenses=["all"],
        max_sentence_words=40,
        allow_passive=True,
        allow_conditionals=True,
        allow_subordinate_clauses=True,
    ),
    CEFRLevel.C2: CEFRRules(
        allowed_tenses=["all"],
        max_sentence_words=999,
        allow_passive=True,
        allow_conditionals=True,
        allow_subordinate_clauses=True,
    ),
}
