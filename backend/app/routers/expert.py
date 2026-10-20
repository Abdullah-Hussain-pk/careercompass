"""
CareerCompass – Expert submission router (FR-16).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_expert
from app.models.models import User, ExpertSubmission
from app.schemas.schemas import ExpertSubmissionCreate, ExpertSubmissionOut

router = APIRouter(prefix="/expert", tags=["Expert Submissions"])


@router.post("/submissions", response_model=ExpertSubmissionOut, status_code=201)
async def submit_career_update(
    body: ExpertSubmissionCreate,
    current_user: User = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> ExpertSubmissionOut:
    """
    Submit a career data update (FR-16).
    Stays unpublished (status=pending) until an admin approves/rejects.
    """
    submission = ExpertSubmission(
        expert_id=current_user.id,
        career_id=body.career_id,
        submission_type=body.submission_type,
        payload=body.payload,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return ExpertSubmissionOut.model_validate(submission)


@router.get("/submissions", response_model=List[ExpertSubmissionOut])
async def list_my_submissions(
    current_user: User = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> List[ExpertSubmissionOut]:
    """List all submissions made by this expert."""
    result = await db.execute(
        select(ExpertSubmission)
        .where(ExpertSubmission.expert_id == current_user.id)
        .order_by(ExpertSubmission.submitted_at.desc())
    )
    return [ExpertSubmissionOut.model_validate(s) for s in result.scalars().all()]
