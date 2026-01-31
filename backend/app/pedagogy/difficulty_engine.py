from app.pedagogy.cefr.levels import CEFRLevel
from app.pedagogy.cefr.rules import CEFR_RULES


def apply_difficulty_engine(text: str, level: str) -> dict:
    """
    Applies CEFR constraints to raw generated text.

    Returns instructions for LLM rewriting.
    """

    cefr_level = CEFRLevel(level)
    rules = CEFR_RULES[cefr_level]

    sentences = [
        s.strip()
        for s in text.replace("!", ".").replace("?", ".").split(".")
        if s.strip()
    ]

    length_violations = []

    for sentence in sentences:
        words = sentence.split()
        if len(words) > rules.max_sentence_words:
            length_violations.append(sentence)

    instruction = f"""
CEFR LEVEL: {cefr_level.value}

RULES:
- Maximum words per sentence: {rules.max_sentence_words}
- Allowed tenses: {", ".join(rules.allowed_tenses)}
- Passive allowed: {rules.allow_passive}
- Conditionals allowed: {rules.allow_conditionals}
- Subordinate clauses allowed: {rules.allow_subordinate_clauses}

STRICT MODE:
You must rewrite the text so that ALL sentences follow CEFR rules.
If something is forbidden, rephrase it using allowed grammar only.
"""

    return {
        "level": cefr_level.value,
        "sentence_count": len(sentences),
        "length_violations": length_violations,
        "instruction": instruction.strip(),
    }
