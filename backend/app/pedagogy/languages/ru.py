from .base import LanguageProfile

LANGUAGE = LanguageProfile(
    code="ru",
    name="Russian",
    script="cyrillic",
    sentence_order="flexible",
    articles=False,
    cases=True,
    genders=3,
    politeness=True,
)
