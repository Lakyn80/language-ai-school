from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LevelRules:
    level: str
    max_sentence_words: int
    allowed_tenses: List[str]
    allowed_structures: List[str]
    forbidden_structures: List[str]
    description: str


LEVELS = {
    "A1": LevelRules(
        level="A1",
        max_sentence_words=8,
        allowed_tenses=[
            "present_simple",
            "to_be_present",
        ],
        allowed_structures=[
            "subject_verb_object",
            "simple_questions",
            "simple_negation",
        ],
        forbidden_structures=[
            "past_simple",
            "future",
            "present_perfect",
            "passive",
            "conditionals",
            "reported_speech",
            "relative_clauses",
        ],
        description="Basic survival language. Short sentences. Present tense only.",
    ),

    "A2": LevelRules(
        level="A2",
        max_sentence_words=12,
        allowed_tenses=[
            "present_simple",
            "past_simple",
            "going_to_future",
        ],
        allowed_structures=[
            "basic_conjunctions",
            "comparatives",
            "countable_uncountable",
        ],
        forbidden_structures=[
            "present_perfect",
            "passive",
            "conditionals",
            "reported_speech",
        ],
        description="Everyday situations. Simple past and basic future.",
    ),

    "B1": LevelRules(
        level="B1",
        max_sentence_words=18,
        allowed_tenses=[
            "present_simple",
            "past_simple",
            "future",
            "present_perfect_basic",
        ],
        allowed_structures=[
            "because_clauses",
            "basic_conditionals",
            "opinions",
        ],
        forbidden_structures=[
            "advanced_passive",
            "reported_speech_advanced",
            "complex_conditionals",
        ],
        description="Independent user. Can explain experiences and opinions.",
    ),

    "B2": LevelRules(
        level="B2",
        max_sentence_words=28,
        allowed_tenses=[
            "all_basic_tenses",
            "present_perfect",
            "passive",
            "conditionals_0_1_2",
        ],
        allowed_structures=[
            "complex_sentences",
            "linking_words",
            "argumentation",
        ],
        forbidden_structures=[
            "c1_academic_style",
            "rare_idioms",
        ],
        description="Upper-intermediate. Clear structured communication.",
    ),
}
