from .base import LanguageProfile

LANGUAGE = LanguageProfile(
    code="es",
    name="Spanish",
    script="latin",
    sentence_order="SVO",
    articles=True,
    cases=False,
    genders=2,
    politeness=True,
)
