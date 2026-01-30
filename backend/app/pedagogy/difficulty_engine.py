import re
from typing import Dict, List

from app.pedagogy.levels import LEVELS, LevelRules


_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")


def split_sentences(text: str) -> List[str]:
    return [
        s.strip()
        for s in _SENTENCE_SPLIT_RE.split(text)
        if s.strip()
    ]


def count_words(sentence: str) -> int:
    return len(re.findall(r"\b\w+\b", sentence))


def validate_sentence_length(
    sentences: List[str],
    rules: LevelRules,
) -> List[str]:
    violations = []

    for s in sentences:
        if count_words(s) > rules.max_sentence_words:
            violations.append(s)

    return violations


def build_level_instruction(rules: LevelRules) -> str:
    return f"""
LEVEL CONSTRAINTS ({rules.level}):

- Maximum {rules.max_sentence_words} words per sentence.
- Allowed tenses: {", ".join(rules.allowed_tenses)}.
- Allowed structures: {", ".join(rules.allowed_structures)}.
- Forbidden structures: {", ".join(rules.forbidden_structures)}.

You must strictly follow these rules.
If a structure is forbidden, rewrite the sentence using allowed grammar only.
""".strip()


def apply_difficulty_engine(
    text: str,
    level: str,
) -> Dict:
    if level not in LEVELS:
        raise ValueError(f"Unknown level: {level}")

    rules = LEVELS[level]

    sentences = split_sentences(text)

    length_violations = validate_sentence_length(
        sentences,
        rules,
    )

    return {
        "level": level,
        "sentence_count": len(sentences),
        "length_violations": length_violations,
        "instruction": build_level_instruction(rules),
    }
