from .base import LanguageProfile

LANGUAGE = LanguageProfile(
    code="cs",
    name="Czech",
    script="latin",
    sentence_order="flexible",
    articles=False,
    cases=True,
    genders=3,
    politeness=True,
)
