from .en import LANGUAGE as EN
from .es import LANGUAGE as ES
from .de import LANGUAGE as DE
from .ru import LANGUAGE as RU
from .cs import LANGUAGE as CS


LANGUAGE_REGISTRY = {
    "en": EN,
    "es": ES,
    "de": DE,
    "ru": RU,
    "cs": CS,
}


def get_language(code: str):
    if not code:
        return EN

    lang = LANGUAGE_REGISTRY.get(code.lower())
    if lang is None:
        raise ValueError(f"Unsupported language: {code}")

    return lang
