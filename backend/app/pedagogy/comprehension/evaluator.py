import re
from difflib import SequenceMatcher
from typing import Any

_model = None
_model_load_failed = False


def get_model() -> Any:
    global _model, _model_load_failed
    if _model is not None:
        return _model
    if _model_load_failed:
        return None

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _model_load_failed = True
        return None

    return _model


def _fallback_similarity(text_a: str, text_b: str) -> float:
    tokens_a = set(re.findall(r"\w+", text_a.lower()))
    tokens_b = set(re.findall(r"\w+", text_b.lower()))

    if not tokens_a or not tokens_b:
        return 0.0

    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    ratio = SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()
    score = (0.65 * jaccard) + (0.35 * ratio)
    return max(0.0, min(score, 1.0))


def semantic_similarity(text_a: str, text_b: str) -> float:
    model = get_model()
    if model is None:
        return _fallback_similarity(text_a, text_b)

    from sklearn.metrics.pairwise import cosine_similarity

    embeddings = model.encode(
        [text_a, text_b],
        normalize_embeddings=True,
    )

    return float(
        cosine_similarity(
            [embeddings[0]],
            [embeddings[1]],
        )[0][0]
    )
