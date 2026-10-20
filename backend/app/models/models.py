"""
CareerCompass – All SQLAlchemy ORM models.

Table list (matches ER diagram in docs/er-diagram.md):
  users, student_profiles, assessments, assessment_answers,
  riasec_scores, skills, student_skill_ratings, careers,
  career_skills, career_degrees, degrees, recommendations,
  recommendation_feedback, availability_slots, bookings,
  consents, session_notes, notifications, expert_submissions,
  settings, audit_log
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Users & roles
# ---------------------------------------------------------------------------

class User(Base):
    """
    Core user account. Exactly one role per account (FR-2).
    Gender is intentionally NOT stored (NFR-9 – fairness).
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum("student", "counsellor", "admin", "expert", name="user_role"),
        nullable=False,
        default="student",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # ── Relationships ─────────────────────────────────────────────
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    assessments: Mapped[List["Assessment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    availability_slots: Mapped[List["AvailabilitySlot"]] = relationship(
        back_populates="counsellor", cascade="all, delete-orphan"
    )
    bookings_as_student: Mapped[List["Booking"]] = relationship(
        "Booking", foreign_keys="Booking.student_id", back_populates="student",
        cascade="all, delete-orphan"
    )
    bookings_as_counsellor: Mapped[List["Booking"]] = relationship(
        "Booking", foreign_keys="Booking.counsellor_id", back_populates="counsellor"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    expert_submissions: Mapped[List["ExpertSubmission"]] = relationship(
        back_populates="expert", cascade="all, delete-orphan"
    )


class StudentProfile(Base):
    """
    Optional academic context for a student (FR-6).
    No gender field – NFR-9.
    """
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    degree_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("degrees.id"), nullable=True
    )
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # optional, NFR-4

    # ── Relationships ─────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="student_profile")
    degree: Mapped[Optional["Degree"]] = relationship()
    skill_ratings: Mapped[List["StudentSkillRating"]] = relationship(
        back_populates="student_profile", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Assessment
# ---------------------------------------------------------------------------

class Assessment(Base):
    """
    One assessment session per student.
    Supports save-and-resume (status field, FR-3/NFR-5).
    """
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum("in_progress", "completed", name="assessment_status"),
        default="in_progress",
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    student: Mapped["User"] = relationship(back_populates="assessments")
    answers: Mapped[List["AssessmentAnswer"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    riasec_score: Mapped[Optional["RIASECScore"]] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class RIASECQuestion(Base):
    """
    48 RIASEC questions, 8 per type (FR-3).
    """
    __tablename__ = "riasec_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    riasec_type: Mapped[str] = mapped_column(
        SAEnum("R", "I", "A", "S", "E", "C", name="riasec_type"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-48 display order

    answers: Mapped[List["AssessmentAnswer"]] = relationship(back_populates="question")


class AssessmentAnswer(Base):
    """Individual 1-5 Likert answer to one RIASEC question."""
    __tablename__ = "assessment_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("riasec_questions.id"), nullable=False
    )
    answer: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5

    __table_args__ = (
        UniqueConstraint("assessment_id", "question_id", name="uq_assessment_question"),
    )

    # ── Relationships ─────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(back_populates="answers")
    question: Mapped["RIASECQuestion"] = relationship(back_populates="answers")


class RIASECScore(Base):
    """
    Computed RIASEC scores (0-100 each) after assessment submission (FR-4).
    Normalised: (sum - min) / (max - min) * 100 per type.
    """
    __tablename__ = "riasec_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Six RIASEC dimensions
    realistic: Mapped[float] = mapped_column(Float, nullable=False)
    investigative: Mapped[float] = mapped_column(Float, nullable=False)
    artistic: Mapped[float] = mapped_column(Float, nullable=False)
    social: Mapped[float] = mapped_column(Float, nullable=False)
    enterprising: Mapped[float] = mapped_column(Float, nullable=False)
    conventional: Mapped[float] = mapped_column(Float, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    assessment: Mapped["Assessment"] = relationship(back_populates="riasec_score")


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

class Skill(Base):
    """A technology/soft skill that students rate and careers require."""
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student_ratings: Mapped[List["StudentSkillRating"]] = relationship(back_populates="skill")
    career_requirements: Mapped[List["CareerSkill"]] = relationship(back_populates="skill")
    learning_resources: Mapped[List["LearningResource"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class StudentSkillRating(Base):
    """Student's self-reported skill level 1-5 (FR-5)."""
    __tablename__ = "student_skill_ratings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    student_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("student_profile_id", "skill_id", name="uq_student_skill"),
    )

    student_profile: Mapped["StudentProfile"] = relationship(back_populates="skill_ratings")
    skill: Mapped["Skill"] = relationship(back_populates="student_ratings")


class LearningResource(Base):
    """Curated free learning resource for a skill (FR-11). Links must be verified."""
    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)

    skill: Mapped["Skill"] = relationship(back_populates="learning_resources")


# ---------------------------------------------------------------------------
# Degrees & Careers
# ---------------------------------------------------------------------------

class Degree(Base):
    """Degree program (e.g., BS Software Engineering)."""
    __tablename__ = "degrees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    career_degrees: Mapped[List["CareerDegree"]] = relationship(back_populates="degree")


class Career(Base):
    """
    A career entry. RIASEC profiles marked as
    'estimated from O*NET categories, to be reviewed by an expert' (see docs).
    """
    __tablename__ = "careers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # RIASEC profile (0-100 scale, estimated from O*NET)
    r_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    i_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    a_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    s_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    e_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    c_score: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)

    # Pakistan-specific context
    typical_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # ── Relationships ─────────────────────────────────────────────
    required_skills: Mapped[List["CareerSkill"]] = relationship(
        back_populates="career", cascade="all, delete-orphan"
    )
    eligible_degrees: Mapped[List["CareerDegree"]] = relationship(
        back_populates="career", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(back_populates="career")


class CareerSkill(Base):
    """Required skill level for a career."""
    __tablename__ = "career_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    career_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("careers.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id"), nullable=False
    )
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5

    __table_args__ = (
        UniqueConstraint("career_id", "skill_id", name="uq_career_skill"),
    )

    career: Mapped["Career"] = relationship(back_populates="required_skills")
    skill: Mapped["Skill"] = relationship(back_populates="career_requirements")


class CareerDegree(Base):
    """Eligible degrees for a career."""
    __tablename__ = "career_degrees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    career_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("careers.id", ondelete="CASCADE"), nullable=False
    )
    degree_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("degrees.id"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("career_id", "degree_id", name="uq_career_degree"),
    )

    career: Mapped["Career"] = relationship(back_populates="eligible_degrees")
    degree: Mapped["Degree"] = relationship(back_populates="career_degrees")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class Recommendation(Base):
    """
    Top-10 career recommendations generated after assessment (FR-7/FR-8).
    factor_breakdown stores the contribution of each scoring term (FR-9).
    """
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    career_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("careers.id"), nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)          # 1-10
    match_score: Mapped[float] = mapped_column(Float, nullable=False)   # 0-100

    # JSON: {"interest": 0.42, "skill": 0.28, "degree": 0.18,
    #        "interest_similarity": 0.84, "skill_coverage": 0.93,
    #        "degree_eligibility": 0.9, "top3_explanation": [...]}
    factor_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    variant: Mapped[str] = mapped_column(
        SAEnum("hybrid", "interest_only", "skill_only", name="rec_variant"),
        default="hybrid",
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # ── Relationships ─────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(back_populates="recommendations")
    career: Mapped["Career"] = relationship(back_populates="recommendations")
    feedback: Mapped[Optional["RecommendationFeedback"]] = relationship(
        back_populates="recommendation", uselist=False, cascade="all, delete-orphan"
    )


class RecommendationFeedback(Base):
    """Student marks recommendation as relevant/not-relevant (FR-19)."""
    __tablename__ = "recommendation_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    recommendation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recommendations.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    is_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 1-5 optional
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    recommendation: Mapped["Recommendation"] = relationship(back_populates="feedback")


# ---------------------------------------------------------------------------
# Booking & Counselling
# ---------------------------------------------------------------------------

class AvailabilitySlot(Base):
    """
    30-minute slot published by a counsellor (FR-12).
    Unique constraint on (counsellor_id, start_time) prevents duplicate slots.
    """
    __tablename__ = "availability_slots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    counsellor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # end_time is always start_time + 30 minutes; stored for query convenience
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    __table_args__ = (
        UniqueConstraint("counsellor_id", "start_time", name="uq_counsellor_slot"),
        Index("ix_slot_counsellor_time", "counsellor_id", "start_time"),
    )

    counsellor: Mapped["User"] = relationship(back_populates="availability_slots")
    booking: Mapped[Optional["Booking"]] = relationship(
        back_populates="slot", uselist=False, cascade="all, delete-orphan"
    )


class Booking(Base):
    """
    Student books a counsellor slot (FR-13).
    DB unique constraint on slot_id prevents double-booking.
    """
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    slot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("availability_slots.id", ondelete="CASCADE"),
        unique=True, nullable=False,  # DB-level prevention of double-booking (FR-13)
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    counsellor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum("confirmed", "cancelled", name="booking_status"),
        default="confirmed",
    )
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    slot: Mapped["AvailabilitySlot"] = relationship(back_populates="booking")
    student: Mapped["User"] = relationship(
        "User", foreign_keys=[student_id], back_populates="bookings_as_student"
    )
    counsellor: Mapped["User"] = relationship(
        "User", foreign_keys=[counsellor_id], back_populates="bookings_as_counsellor"
    )
    consent: Mapped[Optional["Consent"]] = relationship(
        back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )
    session_note: Mapped[Optional["SessionNote"]] = relationship(
        back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )


class Consent(Base):
    """
    Student grants/revokes consent for a counsellor to view results (FR-15).
    Consent is per-booking, not per-counsellor.
    """
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    booking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    booking: Mapped["Booking"] = relationship(back_populates="consent")


class SessionNote(Base):
    """Counsellor's notes after a session."""
    __tablename__ = "session_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    booking_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True, nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    booking: Mapped["Booking"] = relationship(back_populates="session_note")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(Base):
    """In-app notification (FR-14)."""
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="notifications")


# ---------------------------------------------------------------------------
# Expert Submissions
# ---------------------------------------------------------------------------

class ExpertSubmission(Base):
    """
    An industry expert submits a career data update (FR-16).
    Stays unpublished (status='pending') until an admin approves/rejects.
    """
    __tablename__ = "expert_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    expert_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    career_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("careers.id"), nullable=True  # null = new career proposal
    )
    submission_type: Mapped[str] = mapped_column(
        SAEnum("update", "new", name="submission_type"), default="update"
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "approved", "rejected", name="submission_status"),
        default="pending", index=True,
    )
    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    expert: Mapped["User"] = relationship(back_populates="expert_submissions")


# ---------------------------------------------------------------------------
# Settings (recommendation weights)
# ---------------------------------------------------------------------------

class Setting(Base):
    """
    Key-value settings table. Stores recommendation weights w1/w2/w3.
    Editable by admin without code changes (NFR-7).
    """
    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class AuditLog(Base):
    """Immutable audit trail of sensitive operations."""
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
