import re
from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity

from .evaluator import get_model


def split_sentences(text: str) -> List[str]:
    return [
        s.strip()
        for s in text.replace('!', '.').replace('?', '.').split('.')
        if s.strip()
    ]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _max_token_overlap(sentence: str, candidates: List[str]) -> float:
    sentence_tokens = _tokens(sentence)
    if not sentence_tokens:
        return 0.0

    best = 0.0
    for candidate in candidates:
        candidate_tokens = _tokens(candidate)
        if not candidate_tokens:
            continue
        score = len(sentence_tokens & candidate_tokens) / len(
            sentence_tokens | candidate_tokens
        )
        if score > best:
            best = score
    return best


def extract_missing_and_hallucinations(
    original_text: str,
    student_text: str,
    threshold: float = 0.55,
) -> Tuple[List[str], List[str]]:
    """
    Returns:
        missing_sentences
        hallucinated_sentences
    """

    original_sentences = split_sentences(original_text)
    student_sentences = split_sentences(student_text)

    if not original_sentences or not student_sentences:
        return [], []

    model = get_model()
    if model is None:
        lexical_threshold = 0.25
        missing = [
            sentence
            for sentence in original_sentences
            if _max_token_overlap(sentence, student_sentences) < lexical_threshold
        ]
        hallucinated = [
            sentence
            for sentence in student_sentences
            if _max_token_overlap(sentence, original_sentences) < lexical_threshold
        ]
        return missing, hallucinated

    original_embeddings = model.encode(original_sentences)
    student_embeddings = model.encode(student_sentences)

    similarity_matrix = cosine_similarity(
        original_embeddings,
        student_embeddings,
    )

    missing = []
    hallucinated = []

    # original → student
    for i, row in enumerate(similarity_matrix):
        if max(row) < threshold:
            missing.append(original_sentences[i])

    # student → original
    for j, col in enumerate(similarity_matrix.T):
        if max(col) < threshold:
            hallucinated.append(student_sentences[j])

    return missing, hallucinated
