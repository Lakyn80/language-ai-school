from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer('all-MiniLM-L6-v2')


def split_sentences(text: str) -> List[str]:
    return [
        s.strip()
        for s in text.replace('!', '.').replace('?', '.').split('.')
        if s.strip()
    ]


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
