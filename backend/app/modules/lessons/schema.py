import re

from pydantic import BaseModel, Field, model_validator
from typing import List

from app.pedagogy.cefr.levels import CEFRLevel
from app.pedagogy.cefr.rules import CEFR_RULES

MAX_SENTENCES_BY_LEVEL = {
    "A1": 15,
    "A2": 18,
    "B1": 24,
    "B2": 30,
    "C1": 45,
    "C2": 60,
}

FORBIDDEN_GRAMMAR_MARKERS = {
    "A1": [
        " if ",
        " because ",
        " although ",
        " which ",
        " unless ",
    ],
    "A2": [
        " although ",
        " unless ",
        " whereas ",
        " in case ",
    ],
    "B1": [
        " had it not ",
        " were it not ",
        " notwithstanding ",
    ],
}


class VocabularyItem(BaseModel):
    word: str = Field(..., min_length=1)
    meaning: str = Field(..., min_length=1)


class LessonResponse(BaseModel):
    level: str
    story: str
    vocabulary: List[VocabularyItem]
    questions: List[str]
    writing_task: str

    @model_validator(mode="after")
    def validate_story_rules(self):
        level_value = self.level.upper()
        try:
            cefr_level = CEFRLevel(level_value)
        except ValueError as exc:
            raise ValueError(f"Unsupported CEFR level: {self.level}") from exc

        sentences = [
            sentence.strip()
            for sentence in re.split(r"[.!?]+", self.story)
            if sentence.strip()
        ]

        max_sentences = MAX_SENTENCES_BY_LEVEL[cefr_level.value]
        if len(sentences) > max_sentences:
            raise ValueError(
                f"Story exceeds sentence limit for {cefr_level.value}: "
                f"{len(sentences)} > {max_sentences}"
            )

        max_words_per_sentence = CEFR_RULES[cefr_level].max_sentence_words
        for sentence in sentences:
            words = sentence.split()
            if len(words) > max_words_per_sentence:
                raise ValueError(
                    f"Sentence exceeds CEFR word limit ({len(words)} > "
                    f"{max_words_per_sentence})"
                )

        lowered_story = f" {self.story.lower()} "
        for marker in FORBIDDEN_GRAMMAR_MARKERS.get(cefr_level.value, []):
            if marker in lowered_story:
                raise ValueError(
                    f"Forbidden grammar marker for {cefr_level.value}: '{marker.strip()}'"
                )

        self.level = cefr_level.value
        return self
