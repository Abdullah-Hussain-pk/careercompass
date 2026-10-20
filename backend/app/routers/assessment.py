"""
CareerCompass – Assessment router.
Handles RIASEC questionnaire (FR-3), scoring (FR-4),
skill ratings (FR-5), and profile updates (FR-6).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_student
from app.models.models import (
    User, StudentProfile, Assessment, RIASECQuestion,
    AssessmentAnswer, RIASECScore, Skill, StudentSkillRating
)
from app.schemas.schemas import (
    RIASECQuestionOut, AssessmentProgressSave, AssessmentSubmit,
    AssessmentOut, RIASECScoreOut, SkillOut, SkillRatingsSubmit,
    StudentSkillRatingOut, StudentProfileUpdate, StudentProfileOut
)
from app.services.assessment.scoring import compute_riasec_scores

router = APIRouter(prefix="/assessment", tags=["Assessment"])


# ── Profile ────────────────────────────────────────────────────────────────

@router.get("/profile", response_model=StudentProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileOut:
    """Return the student's profile (degree, semester, CGPA)."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return StudentProfileOut.model_validate(profile)


@router.patch("/profile", response_model=StudentProfileOut)
async def update_profile(
    body: StudentProfileUpdate,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> StudentProfileOut:
    """Update optional academic context (FR-6)."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return StudentProfileOut.model_validate(profile)


# ── RIASEC Questions ────────────────────────────────────────────────────────

@router.get("/questions", response_model=List[RIASECQuestionOut])
async def get_questions(db: AsyncSession = Depends(get_db)) -> List[RIASECQuestionOut]:
    """
    Return all 48 RIASEC questions ordered by order_index.
    No auth required – questions are public.
    """
    result = await db.execute(
        select(RIASECQuestion).order_by(RIASECQuestion.order_index)
    )
    questions = result.scalars().all()
    return [RIASECQuestionOut.model_validate(q) for q in questions]


# ── Assessment session ──────────────────────────────────────────────────────

@router.post("/start", response_model=AssessmentOut, status_code=201)
async def start_or_resume_assessment(
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> AssessmentOut:
    """
    Start a new assessment or return the existing in-progress one.
    Supports save-and-resume (NFR-5 / FR-3).
    """
    result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "in_progress")
        .options(selectinload(Assessment.riasec_score))
    )
    existing = result.scalar_one_or_none()
    if existing:
        return AssessmentOut.model_validate(existing)

    assessment = Assessment(student_id=current_user.id)
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return AssessmentOut.model_validate(assessment)


@router.post("/progress", response_model=AssessmentOut)
async def save_progress(
    body: AssessmentProgressSave,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> AssessmentOut:
    """
    Save partial answers (FR-3, NFR-5 – completable in 15 min, resume supported).
    Upserts answers so re-sending a question_id updates the answer.
    """
    result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "in_progress")
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="No in-progress assessment found. POST /start first.")

    # Load existing answers for upsert
    existing_result = await db.execute(
        select(AssessmentAnswer).where(AssessmentAnswer.assessment_id == assessment.id)
    )
    existing_map = {a.question_id: a for a in existing_result.scalars().all()}

    for item in body.answers:
        if item.question_id in existing_map:
            existing_map[item.question_id].answer = item.answer
        else:
            db.add(AssessmentAnswer(
                assessment_id=assessment.id,
                question_id=item.question_id,
                answer=item.answer,
            ))

    await db.commit()
    await db.refresh(assessment)
    return AssessmentOut.model_validate(assessment)


@router.get("/progress", response_model=dict)
async def get_progress(
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return current progress: how many answers saved out of 48."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "in_progress")
        .options(selectinload(Assessment.answers))
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        return {"answered": 0, "total": 48, "assessment_id": None}
    answers_with_vals = {a.question_id: a.answer for a in assessment.answers}
    return {
        "assessment_id": assessment.id,
        "answered": len(assessment.answers),
        "total": 48,
        "saved_answers": answers_with_vals,
    }


@router.post("/submit", response_model=AssessmentOut, status_code=201)
async def submit_assessment(
    body: AssessmentSubmit,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> AssessmentOut:
    """
    Submit all 48 answers; compute and store RIASEC scores (FR-4).
    Normalisation: (sum - min_possible) / (max_possible - min_possible) * 100
    min_possible = 8 (8 questions * 1), max_possible = 40 (8 * 5).
    """
    result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "in_progress")
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="No in-progress assessment found")

    # Validate all question IDs exist
    q_result = await db.execute(select(RIASECQuestion))
    all_questions = {q.id: q for q in q_result.scalars().all()}

    for item in body.answers:
        if item.question_id not in all_questions:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown question_id: {item.question_id}",
            )

    # Save all answers (upsert)
    existing_result = await db.execute(
        select(AssessmentAnswer).where(AssessmentAnswer.assessment_id == assessment.id)
    )
    existing_map = {a.question_id: a for a in existing_result.scalars().all()}

    for item in body.answers:
        if item.question_id in existing_map:
            existing_map[item.question_id].answer = item.answer
        else:
            db.add(AssessmentAnswer(
                assessment_id=assessment.id,
                question_id=item.question_id,
                answer=item.answer,
            ))

    # Compute RIASEC scores
    type_sums = {"R": [], "I": [], "A": [], "S": [], "E": [], "C": []}
    for item in body.answers:
        q = all_questions[item.question_id]
        type_sums[q.riasec_type].append(item.answer)

    scores = compute_riasec_scores(type_sums)

    # Delete old score if resubmitting
    old_score = await db.execute(
        select(RIASECScore).where(RIASECScore.assessment_id == assessment.id)
    )
    old = old_score.scalar_one_or_none()
    if old:
        await db.delete(old)

    riasec_score = RIASECScore(
        assessment_id=assessment.id,
        realistic=scores["R"],
        investigative=scores["I"],
        artistic=scores["A"],
        social=scores["S"],
        enterprising=scores["E"],
        conventional=scores["C"],
    )
    db.add(riasec_score)

    from datetime import datetime, timezone
    assessment.status = "completed"
    assessment.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(assessment)
    # Load the score relationship
    result2 = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment.id)
        .options(selectinload(Assessment.riasec_score))
    )
    assessment = result2.scalar_one()
    return AssessmentOut.model_validate(assessment)


@router.get("/my-results", response_model=AssessmentOut)
async def get_my_results(
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> AssessmentOut:
    """Return the student's most recent completed assessment with RIASEC scores."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == current_user.id)
        .where(Assessment.status == "completed")
        .options(selectinload(Assessment.riasec_score))
        .order_by(Assessment.completed_at.desc())
    )
    assessment = result.scalars().first()
    if not assessment:
        raise HTTPException(status_code=404, detail="No completed assessment found")
    return AssessmentOut.model_validate(assessment)


# ── Skills ─────────────────────────────────────────────────────────────────

@router.get("/skills", response_model=List[SkillOut])
async def list_skills(db: AsyncSession = Depends(get_db)) -> List[SkillOut]:
    """Return all available skills for rating."""
    result = await db.execute(select(Skill).order_by(Skill.name))
    return [SkillOut.model_validate(s) for s in result.scalars().all()]


@router.post("/skills/rate", response_model=List[StudentSkillRatingOut], status_code=201)
async def rate_skills(
    body: SkillRatingsSubmit,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> List[StudentSkillRatingOut]:
    """
    Student rates at least 10 skills 1-5 (FR-5).
    Upserts ratings so re-submitting updates existing ones.
    """
    # Get student profile
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Validate skill IDs
    skill_ids = [item.skill_id for item in body.ratings]
    skills_result = await db.execute(select(Skill).where(Skill.id.in_(skill_ids)))
    found_skills = {s.id: s for s in skills_result.scalars().all()}

    for item in body.ratings:
        if item.skill_id not in found_skills:
            raise HTTPException(status_code=422, detail=f"Unknown skill_id: {item.skill_id}")

    # Load existing ratings for upsert
    existing_result = await db.execute(
        select(StudentSkillRating).where(StudentSkillRating.student_profile_id == profile.id)
    )
    existing_map = {r.skill_id: r for r in existing_result.scalars().all()}

    for item in body.ratings:
        if item.skill_id in existing_map:
            existing_map[item.skill_id].rating = item.rating
        else:
            db.add(StudentSkillRating(
                student_profile_id=profile.id,
                skill_id=item.skill_id,
                rating=item.rating,
            ))

    await db.commit()

    # Return updated ratings
    updated_result = await db.execute(
        select(StudentSkillRating, Skill)
        .join(Skill, StudentSkillRating.skill_id == Skill.id)
        .where(StudentSkillRating.student_profile_id == profile.id)
    )
    return [
        StudentSkillRatingOut(
            skill_id=sr.skill_id,
            skill_name=sk.name,
            rating=sr.rating,
        )
        for sr, sk in updated_result.all()
    ]


@router.get("/skills/my-ratings", response_model=List[StudentSkillRatingOut])
async def get_my_skill_ratings(
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> List[StudentSkillRatingOut]:
    """Return all of this student's skill ratings."""
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        return []

    result = await db.execute(
        select(StudentSkillRating, Skill)
        .join(Skill, StudentSkillRating.skill_id == Skill.id)
        .where(StudentSkillRating.student_profile_id == profile.id)
    )
    return [
        StudentSkillRatingOut(
            skill_id=sr.skill_id,
            skill_name=sk.name,
            rating=sr.rating,
        )
        for sr, sk in result.all()
    ]
