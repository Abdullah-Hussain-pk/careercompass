"""
CareerCompass – Evaluation module (FR-18 / Recommendation Engine evaluation).

Computes precision@5 and nDCG@5 from real student feedback stored in DB.
Data source: recommendation_feedback table (FR-19).

HONESTY NOTE: This computes from actual feedback only.
Do NOT add synthetic data here. Use seed_demo_feedback.py for demos only.
"""
import math
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Recommendation, RecommendationFeedback, Assessment
from app.schemas.schemas import EvaluationResult


async def compute_evaluation(db: AsyncSession) -> List[EvaluationResult]:
    """
    Compute precision@5 and nDCG@5 per recommendation variant.

    Definitions:
        precision@5 = (number of relevant items in top 5) / 5
        nDCG@5      = DCG@5 / IDCG@5
            DCG@5  = Σ (rel_i / log2(i+1)) for i in 1..5
            IDCG@5 = ideal DCG (all relevant items first)

    Only assessments with at least 5 feedbacks are included.
    Returns empty list (not fake data) if no feedback exists.
    """
    results = []

    for variant in ("hybrid", "interest_only", "skill_only"):
        # Load all recommendations for this variant with feedback
        recs_result = await db.execute(
            select(Recommendation, RecommendationFeedback, Assessment)
            .join(RecommendationFeedback, Recommendation.id == RecommendationFeedback.recommendation_id)
            .join(Assessment, Recommendation.assessment_id == Assessment.id)
            .where(Recommendation.variant == variant)
            .order_by(Assessment.student_id, Recommendation.rank)
        )
        rows = recs_result.all()

        if not rows:
            # No feedback for this variant – skip (do not fabricate)
            continue

        # Group by student (assessment)
        student_data: dict[str, list] = {}
        for rec, fb, assess in rows:
            key = assess.student_id
            if key not in student_data:
                student_data[key] = []
            student_data[key].append({
                "rank": rec.rank,
                "is_relevant": fb.is_relevant,
                "rating": fb.rating,
            })

        p5_list = []
        ndcg5_list = []
        rating_list = []

        for student_id, items in student_data.items():
            # Only use first 5 by rank
            top5 = sorted(items, key=lambda x: x["rank"])[:5]
            if len(top5) < 5:
                continue   # skip students with fewer than 5 feedbacks

            # Precision@5
            relevant_count = sum(1 for i in top5 if i["is_relevant"])
            p5 = relevant_count / 5
            p5_list.append(p5)

            # nDCG@5 – binary relevance (is_relevant = 1/0)
            dcg = sum(
                (1 if item["is_relevant"] else 0) / math.log2(rank + 2)  # rank 0-indexed
                for rank, item in enumerate(top5)
            )
            # IDCG: best case = all relevant at the top
            ideal = [1] * relevant_count + [0] * (5 - relevant_count)
            idcg = sum(
                v / math.log2(rank + 2)
                for rank, v in enumerate(ideal)
            )
            ndcg = dcg / idcg if idcg > 0 else 0.0
            ndcg5_list.append(ndcg)

            # Mean rating
            ratings = [i["rating"] for i in top5 if i["rating"] is not None]
            if ratings:
                rating_list.append(sum(ratings) / len(ratings))

        if not p5_list:
            continue

        results.append(EvaluationResult(
            variant=variant,
            precision_at_5=round(sum(p5_list) / len(p5_list), 4),
            ndcg_at_5=round(sum(ndcg5_list) / len(ndcg5_list), 4),
            mean_relevance_rating=round(sum(rating_list) / len(rating_list), 2) if rating_list else None,
            sample_size=len(p5_list),
        ))

    return results
