from typing import Tuple


CEFR_THRESHOLDS = {
    "A1": 0.40,
    "A2": 0.50,
    "B1": 0.65,
    "B2": 0.75,
    "C1": 0.85,
    "C2": 0.92,
}


def evaluate_cefr_similarity(
    level: str,
    similarity: float
) -> Tuple[int, str]:
    """
    Returns:
        score_percent: int
        result: PASS | FAIL
    """

    level = level.upper()

    if level not in CEFR_THRESHOLDS:
        raise ValueError(f"Unsupported CEFR level: {level}")

    threshold = CEFR_THRESHOLDS[level]

    score_percent = int(similarity * 100)

    result = "PASS" if similarity >= threshold else "FAIL"

    return score_percent, result
