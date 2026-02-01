from typing import List


FEEDBACK_TEMPLATES = {
    'en': {
        'PASS': 'You understood the main meaning of the text.',
        'FAIL': 'You did not fully understand the meaning of the text.',
        'MISSING': 'You missed some important information.',
        'HALLUCINATIONS': 'Some details in your summary were not in the original text.',
    },
    'ru': {
        'PASS': 'Ты правильно понял общий смысл текста.',
        'FAIL': 'Ты не полностью понял смысл текста.',
        'MISSING': 'Ты упустил важную информацию.',
        'HALLUCINATIONS': 'В твоём пересказе есть детали, которых не было в тексте.',
    },
    'cs': {
        'PASS': 'Správně jsi pochopil hlavní smysl textu.',
        'FAIL': 'Nepochopil jsi plně smysl textu.',
        'MISSING': 'Chybí některé důležité informace.',
        'HALLUCINATIONS': 'Ve shrnutí jsou informace, které v textu nebyly.',
    },
}


def build_feedback_text(
    native_language: str,
    result: str,
    missing: List[str],
    hallucinations: List[str],
) -> str:
    lang = native_language.lower()

    templates = FEEDBACK_TEMPLATES.get(lang, FEEDBACK_TEMPLATES['en'])

    parts = [templates[result]]

    if missing:
        parts.append(templates['MISSING'])

    if hallucinations:
        parts.append(templates['HALLUCINATIONS'])

    return ' '.join(parts)
