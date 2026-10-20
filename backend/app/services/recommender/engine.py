"""
CareerCompass – Hybrid Recommendation Engine (Core of the project).

Match formula:
    match = w1 * InterestSimilarity + w2 * SkillCoverage + w3 * DegreeEligibility

Where:
    InterestSimilarity = cosine_similarity(student_RIASEC, career_RIASEC)
    SkillCoverage      = Σ min(student_level, req_level) / Σ req_level
    DegreeEligibility  = 1.0 if degree matches, penalty if not, 1.0 if no degree (cold-start)

Weights w1, w2, w3 are stored in the settings table and must sum to 1.0.
All comments are intentionally verbose to help the student explain in a viva.
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_interest_similarity(
    student_riasec: list[float],
    career_riasec: list[float],
) -> float:
    """
    Compute cosine similarity between student and career RIASEC vectors.

    Cosine similarity measures the angle between two vectors.
    A value of 1.0 means perfect alignment; 0.0 means orthogonal (no overlap).
    We use scikit-learn's implementation for numerical stability.

    Args:
        student_riasec: [R, I, A, S, E, C] scores 0-100.
        career_riasec:  [R, I, A, S, E, C] profile 0-100.

    Returns:
        float in [0, 1]. (RIASEC scores are non-negative so negative cosine
        similarity cannot occur in practice.)
    """
    sv = np.array(student_riasec, dtype=float).reshape(1, -1)
    cv = np.array(career_riasec, dtype=float).reshape(1, -1)

    # Handle zero vectors (all scores are 0 → no information)
    if np.linalg.norm(sv) == 0 or np.linalg.norm(cv) == 0:
        return 0.0

    sim = cosine_similarity(sv, cv)[0][0]
    # Clamp to [0, 1] – cosine can be slightly outside due to float precision
    return float(max(0.0, min(1.0, sim)))


def compute_skill_coverage(
    student_ratings: dict[str, int],   # {skill_id: student_level}
    career_requirements: list[dict],   # [{"skill_id": ..., "required_level": ...}]
) -> float:
    """
    Compute skill coverage score.

    Formula:
        coverage = Σ min(student_level, req_level) / Σ req_level

    Intuition: each required skill contributes up to its full required level.
    If the student is rated above the requirement, the contribution is capped
    at the required level (no extra reward for over-qualification).
    A missing skill (not rated) contributes 0.

    Args:
        student_ratings:       mapping of skill_id → student's 1-5 rating.
        career_requirements:   list of dicts with 'skill_id' and 'required_level'.

    Returns:
        float in [0, 1]. Returns 0.0 if career has no required skills.
    """
    if not career_requirements:
        return 1.0  # no requirements → automatically covered

    total_required = sum(r["required_level"] for r in career_requirements)
    if total_required == 0:
        return 1.0

    earned = 0.0
    for req in career_requirements:
        student_level = student_ratings.get(req["skill_id"], 0)
        earned += min(student_level, req["required_level"])

    return earned / total_required


def compute_degree_eligibility(
    student_degree_id: str | None,
    eligible_degree_ids: list[str],
    not_eligible_penalty: float = 0.6,
) -> float:
    """
    Compute degree eligibility score.

    Returns:
        1.0  – student's degree is in the eligible list.
        0.6  – (configurable penalty) student has a degree but it's not eligible.
        1.0  – student has no degree (cold-start: neutral, no penalty).

    The neutral cold-start value means students without a declared degree are
    not disadvantaged, which is fair for early-semester students.

    Args:
        student_degree_id:    the student's degree ID or None.
        eligible_degree_ids:  list of eligible degree IDs for this career.
        not_eligible_penalty: configurable penalty (default 0.6).
    """
    if student_degree_id is None:
        return 1.0  # cold-start: no penalty

    if not eligible_degree_ids:
        return 1.0  # career has no degree restriction

    if student_degree_id in eligible_degree_ids:
        return 1.0

    return not_eligible_penalty


def compute_match_score(
    interest_similarity: float,
    skill_coverage: float,
    degree_eligibility: float,
    w1: float,
    w2: float,
    w3: float,
) -> float:
    """
    Compute the final weighted match score, scaled to 0-100.

    match = (w1 * interest_sim + w2 * skill_cov + w3 * degree_elig) * 100

    Each term contributes proportionally to its weight.

    Args:
        interest_similarity: cosine similarity [0, 1].
        skill_coverage:      coverage ratio [0, 1].
        degree_eligibility:  eligibility value (0.6 or 1.0).
        w1, w2, w3:          weights summing to 1.0.

    Returns:
        float in [0, 100].
    """
    raw = w1 * interest_similarity + w2 * skill_coverage + w3 * degree_eligibility
    return round(min(100.0, max(0.0, raw * 100)), 2)


def build_explanation(
    career_title: str,
    career_riasec: list[float],
    student_riasec: list[float],
    interest_similarity: float,
    skill_coverage: float,
    degree_eligibility: float,
    interest_contribution: float,
    skill_contribution: float,
    degree_contribution: float,
    student_degree_id: str | None,
    eligible_degree_ids: list[str],
    is_cold_start: bool,
) -> list[str]:
    """
    Generate plain-language explanations for the top 3 contributing factors (FR-9).

    Each explanation is a human-readable sentence.
    Sorted by contribution magnitude, largest first.

    Returns a list of up to 3 sentences.
    """
    # Map RIASEC types to their names for readable output
    riasec_names = ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]

    # Find the dominant RIASEC type in the student's profile
    dominant_idx = int(np.argmax(student_riasec))
    dominant_type = riasec_names[dominant_idx]
    dominant_score = student_riasec[dominant_idx]

    # Build individual explanations
    explanations = []

    # Interest explanation
    if interest_similarity >= 0.85:
        explanations.append(
            (interest_contribution,
             f"Your {dominant_type} score ({dominant_score:.0f}) very closely matches "
             f"this career's personality profile (interest match: {interest_similarity*100:.0f}%).")
        )
    elif interest_similarity >= 0.6:
        explanations.append(
            (interest_contribution,
             f"Your interest profile moderately aligns with {career_title} "
             f"({interest_similarity*100:.0f}% interest match).")
        )
    else:
        explanations.append(
            (interest_contribution,
             f"Your interest profile has a partial overlap ({interest_similarity*100:.0f}%) "
             f"with this career – other factors may compensate.")
        )

    # Skill explanation
    if is_cold_start:
        explanations.append(
            (skill_contribution,
             "No skills rated yet – skill matching is skipped (cold-start). "
             "Rate at least 10 skills for a more accurate recommendation.")
        )
    elif skill_coverage >= 0.9:
        explanations.append(
            (skill_contribution,
             f"You already meet {skill_coverage*100:.0f}% of the required skills for this career.")
        )
    elif skill_coverage >= 0.5:
        explanations.append(
            (skill_contribution,
             f"You meet {skill_coverage*100:.0f}% of the required skills; "
             f"there is room to grow in some areas.")
        )
    else:
        explanations.append(
            (skill_contribution,
             f"This career requires skills you haven't fully developed yet "
             f"(coverage: {skill_coverage*100:.0f}%). Check the skill-gap roadmap.")
        )

    # Degree explanation
    if student_degree_id is None:
        explanations.append(
            (degree_contribution,
             "You haven't set a degree program yet – degree eligibility is neutral.")
        )
    elif degree_eligibility == 1.0:
        explanations.append(
            (degree_contribution,
             "Your degree program is a recognised path into this career.")
        )
    else:
        explanations.append(
            (degree_contribution,
             "Your degree program is not the most common entry path for this career, "
             "but it doesn't disqualify you.")
        )

    # Sort by contribution magnitude (highest first) and return top 3 sentences
    explanations.sort(key=lambda x: x[0], reverse=True)
    return [e[1] for e in explanations[:3]]


def rank_careers(
    student_riasec: list[float],
    student_skill_ratings: dict[str, int],     # {skill_id: rating}
    student_degree_id: str | None,
    careers: list[dict],                        # career records with all fields
    w1: float,
    w2: float,
    w3: float,
    not_eligible_penalty: float = 0.6,
    top_n: int = 10,
    variant: str = "hybrid",
) -> list[dict]:
    """
    Rank all active careers and return the top_n.

    This is the main entry point for the recommendation engine.

    Cold-start handling:
        If the student has no skill ratings, skill_coverage defaults to 0
        and w1 effectively absorbs the full weight (interest-only).
        The explanation flags this to the user.

    Args:
        student_riasec:         [R,I,A,S,E,C] scores (0-100).
        student_skill_ratings:  {skill_id: 1-5}.
        student_degree_id:      degree ID or None.
        careers:                list of career dicts (pre-fetched from DB).
        w1, w2, w3:             recommendation weights (must sum to 1.0).
        not_eligible_penalty:   degree penalty (default 0.6).
        top_n:                  how many top careers to return (default 10).
        variant:                "hybrid" | "interest_only" | "skill_only".

    Returns:
        list of result dicts sorted by match_score descending.
    """
    is_cold_start = len(student_skill_ratings) == 0
    results = []

    for career in careers:
        # ── Compute each component ─────────────────────────────────
        career_riasec = [
            career["r_score"], career["i_score"], career["a_score"],
            career["s_score"], career["e_score"], career["c_score"],
        ]

        interest_sim = compute_interest_similarity(student_riasec, career_riasec)

        skill_cov = compute_skill_coverage(
            student_skill_ratings if not is_cold_start else {},
            career["required_skills"],
        )

        degree_elig = compute_degree_eligibility(
            student_degree_id,
            career["eligible_degree_ids"],
            not_eligible_penalty,
        )

        # ── Apply variant weighting ───────────────────────────────
        if variant == "interest_only":
            # Only interest score, normalised by w1 pretending w1=1
            match = compute_match_score(interest_sim, 0.0, 0.0, 1.0, 0.0, 0.0)
            eff_w1, eff_w2, eff_w3 = 1.0, 0.0, 0.0
        elif variant == "skill_only":
            match = compute_match_score(0.0, skill_cov, 0.0, 0.0, 1.0, 0.0)
            eff_w1, eff_w2, eff_w3 = 0.0, 1.0, 0.0
        else:  # hybrid (default)
            match = compute_match_score(interest_sim, skill_cov, degree_elig, w1, w2, w3)
            eff_w1, eff_w2, eff_w3 = w1, w2, w3

        # ── Compute per-term contributions ────────────────────────
        interest_contrib = eff_w1 * interest_sim
        skill_contrib = eff_w2 * skill_cov
        degree_contrib = eff_w3 * degree_elig

        # ── Build explanation ─────────────────────────────────────
        top3 = build_explanation(
            career["title"],
            career_riasec,
            student_riasec,
            interest_sim,
            skill_cov,
            degree_elig,
            interest_contrib,
            skill_contrib,
            degree_contrib,
            student_degree_id,
            career["eligible_degree_ids"],
            is_cold_start,
        )

        results.append({
            "career_id": career["id"],
            "career_title": career["title"],
            "match_score": match,
            "factor_breakdown": {
                "interest_contribution": round(interest_contrib, 4),
                "skill_contribution": round(skill_contrib, 4),
                "degree_contribution": round(degree_contrib, 4),
                "interest_similarity": round(interest_sim, 4),
                "skill_coverage": round(skill_cov, 4),
                "degree_eligibility": round(degree_elig, 4),
                "top3_explanation": top3,
                "is_cold_start": is_cold_start,
            },
        })

    # ── Sort descending by match score ────────────────────────────
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n]
