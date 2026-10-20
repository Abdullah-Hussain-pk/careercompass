"""
CareerCompass – RIASEC scoring service (FR-4).

Normalisation formula:
    score = (raw_sum - min_possible) / (max_possible - min_possible) * 100

For 8 questions on a 1-5 scale:
    min_possible = 8 * 1 = 8
    max_possible = 8 * 5 = 40

This means a student who answers all 1s gets 0 and all 5s gets 100.
"""

QUESTIONS_PER_TYPE = 8
MIN_SCORE = QUESTIONS_PER_TYPE * 1   # = 8
MAX_SCORE = QUESTIONS_PER_TYPE * 5   # = 40


def normalise_score(raw_sum: int) -> float:
    """
    Normalise a raw RIASEC type sum to 0-100 scale.

    Args:
        raw_sum: Sum of answers for one RIASEC type (8 questions, each 1-5).

    Returns:
        float: Normalised score between 0.0 and 100.0.
    """
    if MAX_SCORE == MIN_SCORE:
        return 0.0  # edge case: all same (shouldn't happen)
    score = (raw_sum - MIN_SCORE) / (MAX_SCORE - MIN_SCORE) * 100
    # Clamp to [0, 100] to handle edge cases
    return max(0.0, min(100.0, round(score, 2)))


def compute_riasec_scores(type_answers: dict[str, list[int]]) -> dict[str, float]:
    """
    Compute normalised RIASEC scores from grouped answer lists.

    Args:
        type_answers: dict mapping RIASEC type ('R','I','A','S','E','C')
                      to a list of integer answers (1-5).

    Returns:
        dict mapping type letter to normalised score (0-100).

    Example:
        >>> compute_riasec_scores({"R": [4,5,3,4,5,5,4,3], ...})
        {"R": 82.14, ...}
    """
    scores: dict[str, float] = {}
    for rtype in ("R", "I", "A", "S", "E", "C"):
        answers = type_answers.get(rtype, [])
        if not answers:
            scores[rtype] = 0.0
        else:
            scores[rtype] = normalise_score(sum(answers))
    return scores


def score_vector_from_riasec(riasec_score_obj) -> list[float]:
    """
    Convert a RIASECScore ORM object into an ordered list
    [R, I, A, S, E, C] for cosine similarity computation.
    """
    return [
        riasec_score_obj.realistic,
        riasec_score_obj.investigative,
        riasec_score_obj.artistic,
        riasec_score_obj.social,
        riasec_score_obj.enterprising,
        riasec_score_obj.conventional,
    ]


def career_vector_from_career(career_obj) -> list[float]:
    """Convert a Career ORM object into a [R, I, A, S, E, C] vector."""
    return [
        career_obj.r_score,
        career_obj.i_score,
        career_obj.a_score,
        career_obj.s_score,
        career_obj.e_score,
        career_obj.c_score,
    ]
