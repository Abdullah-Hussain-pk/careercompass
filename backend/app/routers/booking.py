"""
CareerCompass – Booking, slots, and consent router (FR-12 to FR-15).
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import (
    get_current_user, get_current_active_student,
    get_current_counsellor
)
from app.models.models import (
    User, AvailabilitySlot, Booking, Consent, SessionNote,
    Notification, Assessment, RIASECScore
)
from app.schemas.schemas import (
    SlotCreate, SlotOut, SlotWithCounsellorOut, BookingCreate, BookingOut,
    ConsentUpdate, ConsentOut, SessionNoteCreate, SessionNoteOut,
    AssessmentOut, RIASECScoreOut
)

router = APIRouter(prefix="/booking", tags=["Booking & Slots"])


# ── Counsellor Slot Management (FR-12) ─────────────────────────────────────

@router.post("/slots", response_model=SlotOut, status_code=201)
async def create_slot(
    body: SlotCreate,
    current_user: User = Depends(get_current_counsellor),
    db: AsyncSession = Depends(get_db),
) -> SlotOut:
    """Create a 30-minute availability slot (FR-12)."""
    start = body.start_time
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=30)

    slot = AvailabilitySlot(
        counsellor_id=current_user.id,
        start_time=start,
        end_time=end,
    )
    db.add(slot)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Slot already exists at this time")

    await db.refresh(slot)
    return SlotOut.model_validate(slot)


@router.get("/slots/my", response_model=List[SlotOut])
async def get_my_slots(
    current_user: User = Depends(get_current_counsellor),
    db: AsyncSession = Depends(get_db),
) -> List[SlotOut]:
    """Return all slots published by this counsellor."""
    result = await db.execute(
        select(AvailabilitySlot)
        .where(AvailabilitySlot.counsellor_id == current_user.id)
        .order_by(AvailabilitySlot.start_time)
    )
    return [SlotOut.model_validate(s) for s in result.scalars().all()]


@router.delete("/slots/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: str,
    current_user: User = Depends(get_current_counsellor),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an unbooked slot."""
    result = await db.execute(
        select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id)
    )
    slot = result.scalar_one_or_none()
    if not slot or slot.counsellor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=409, detail="Cannot delete a booked slot")
    await db.delete(slot)
    await db.commit()


# ── Public slot listing ────────────────────────────────────────────────────

@router.get("/slots", response_model=List[SlotWithCounsellorOut])
async def list_available_slots(
    counsellor_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SlotWithCounsellorOut]:
    """List all available (not booked) future slots, optionally filtered by counsellor."""
    now = datetime.now(timezone.utc)
    query = (
        select(AvailabilitySlot, User)
        .join(User, AvailabilitySlot.counsellor_id == User.id)
        .where(AvailabilitySlot.is_booked == False)
        .where(AvailabilitySlot.start_time > now)
    )
    if counsellor_id:
        query = query.where(AvailabilitySlot.counsellor_id == counsellor_id)

    query = query.order_by(AvailabilitySlot.start_time)
    result = await db.execute(query)

    return [
        SlotWithCounsellorOut(
            id=slot.id,
            counsellor_id=slot.counsellor_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_booked=slot.is_booked,
            counsellor_name=counsellor.full_name,
        )
        for slot, counsellor in result.all()
    ]


# ── Bookings (FR-13) ───────────────────────────────────────────────────────

@router.post("/bookings", response_model=BookingOut, status_code=201)
async def create_booking(
    body: BookingCreate,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> BookingOut:
    """
    Book a slot (FR-13). Max 4 steps in the frontend.
    Double-booking prevented by:
      1. DB unique constraint on (slot_id) in bookings table.
      2. Transactional update of AvailabilitySlot.is_booked.

    Consent is optionally granted at booking time (FR-15).
    """
    # Load slot with lock
    slot_result = await db.execute(
        select(AvailabilitySlot).where(AvailabilitySlot.id == body.slot_id)
    )
    slot = slot_result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=409, detail="Slot already booked")

    # Mark slot as booked (transactional)
    slot.is_booked = True

    booking = Booking(
        slot_id=slot.id,
        student_id=current_user.id,
        counsellor_id=slot.counsellor_id,
    )
    db.add(booking)
    await db.flush()   # get booking.id

    # Create consent record (granted or not, FR-15)
    consent = Consent(booking_id=booking.id, granted=body.grant_consent)
    db.add(consent)

    # Notifications (FR-14): create for both parties
    student_notif = Notification(
        user_id=current_user.id,
        message=f"Your booking is confirmed for {slot.start_time.strftime('%Y-%m-%d %H:%M')} UTC.",
    )
    counsellor_notif = Notification(
        user_id=slot.counsellor_id,
        message=f"New booking from {current_user.full_name} for {slot.start_time.strftime('%Y-%m-%d %H:%M')} UTC.",
    )
    db.add(student_notif)
    db.add(counsellor_notif)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Slot was booked concurrently; please choose another")

    await db.refresh(booking)
    await db.refresh(slot)

    return BookingOut(
        id=booking.id,
        slot_id=booking.slot_id,
        student_id=booking.student_id,
        counsellor_id=booking.counsellor_id,
        status=booking.status,
        booked_at=booking.booked_at,
        start_time=slot.start_time,
        consent_granted=body.grant_consent,
    )


@router.get("/bookings", response_model=List[BookingOut])
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[BookingOut]:
    """Return bookings for the current user (student or counsellor)."""
    if current_user.role == "student":
        query = (
            select(Booking, AvailabilitySlot, User)
            .join(AvailabilitySlot, Booking.slot_id == AvailabilitySlot.id)
            .join(User, Booking.counsellor_id == User.id)
            .where(Booking.student_id == current_user.id)
        )
    elif current_user.role == "counsellor":
        query = (
            select(Booking, AvailabilitySlot, User)
            .join(AvailabilitySlot, Booking.slot_id == AvailabilitySlot.id)
            .join(User, Booking.student_id == User.id)
            .where(Booking.counsellor_id == current_user.id)
        )
    else:
        raise HTTPException(status_code=403, detail="Students and counsellors only")

    result = await db.execute(query.order_by(AvailabilitySlot.start_time.desc()))

    output = []
    for booking, slot, other_user in result.all():
        consent_res = await db.execute(
            select(Consent).where(Consent.booking_id == booking.id)
        )
        consent = consent_res.scalar_one_or_none()
        output.append(BookingOut(
            id=booking.id,
            slot_id=booking.slot_id,
            student_id=booking.student_id,
            counsellor_id=booking.counsellor_id,
            status=booking.status,
            booked_at=booking.booked_at,
            start_time=slot.start_time,
            counsellor_name=other_user.full_name if current_user.role == "student" else None,
            student_name=other_user.full_name if current_user.role == "counsellor" else None,
            consent_granted=consent.granted if consent else False,
        ))
    return output


@router.delete("/bookings/{booking_id}", status_code=204)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a booking and free up the slot."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if current_user.role == "student" and booking.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "counsellor" and booking.counsellor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    booking.status = "cancelled"
    from datetime import datetime, timezone
    booking.cancelled_at = datetime.now(timezone.utc)

    # Free the slot
    slot_result = await db.execute(select(AvailabilitySlot).where(AvailabilitySlot.id == booking.slot_id))
    slot = slot_result.scalar_one_or_none()
    if slot:
        slot.is_booked = False

    await db.commit()


# ── Consent (FR-15) ────────────────────────────────────────────────────────

@router.patch("/bookings/{booking_id}/consent", response_model=ConsentOut)
async def update_consent(
    booking_id: str,
    body: ConsentUpdate,
    current_user: User = Depends(get_current_active_student),
    db: AsyncSession = Depends(get_db),
) -> ConsentOut:
    """Grant or revoke consent for a counsellor to view assessment results (FR-15)."""
    # Verify student owns this booking
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking or booking.student_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    consent_result = await db.execute(select(Consent).where(Consent.booking_id == booking_id))
    consent = consent_result.scalar_one_or_none()

    if consent:
        consent.granted = body.granted
    else:
        consent = Consent(booking_id=booking_id, granted=body.granted)
        db.add(consent)

    await db.commit()
    await db.refresh(consent)
    return ConsentOut.model_validate(consent)


# ── Counsellor: view student results (only with consent, FR-15) ────────────

@router.get("/bookings/{booking_id}/student-results", response_model=AssessmentOut)
async def get_student_results_with_consent(
    booking_id: str,
    current_user: User = Depends(get_current_counsellor),
    db: AsyncSession = Depends(get_db),
) -> AssessmentOut:
    """
    Counsellor views the student's RIASEC assessment results.
    ONLY accessible if the student has granted consent for this specific booking (FR-15).
    """
    # Load booking and verify counsellor
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking or booking.counsellor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Check consent
    consent_result = await db.execute(select(Consent).where(Consent.booking_id == booking_id))
    consent = consent_result.scalar_one_or_none()
    if not consent or not consent.granted:
        raise HTTPException(
            status_code=403,
            detail="Student has not granted consent to view results for this booking",
        )

    # Load assessment
    assess_result = await db.execute(
        select(Assessment)
        .where(Assessment.student_id == booking.student_id)
        .where(Assessment.status == "completed")
        .options(selectinload(Assessment.riasec_score))
        .order_by(Assessment.completed_at.desc())
    )
    assessment = assess_result.scalars().first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Student has no completed assessment")

    return AssessmentOut.model_validate(assessment)


# ── Session notes ──────────────────────────────────────────────────────────

@router.post("/bookings/{booking_id}/notes", response_model=SessionNoteOut, status_code=201)
async def create_session_note(
    booking_id: str,
    body: SessionNoteCreate,
    current_user: User = Depends(get_current_counsellor),
    db: AsyncSession = Depends(get_db),
) -> SessionNoteOut:
    """Counsellor records session notes after a session."""
    booking_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking or booking.counsellor_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Upsert note
    note_result = await db.execute(select(SessionNote).where(SessionNote.booking_id == booking_id))
    note = note_result.scalar_one_or_none()
    if note:
        note.notes = body.notes
    else:
        note = SessionNote(booking_id=booking_id, notes=body.notes)
        db.add(note)

    await db.commit()
    await db.refresh(note)
    return SessionNoteOut.model_validate(note)


# ── Notifications (FR-14) ─────────────────────────────────────────────────

@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Return unread notifications for the current user."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifs = result.scalars().all()
    return [{"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in notifs]


@router.patch("/notifications/{notif_id}/read", status_code=200)
async def mark_notification_read(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            and_(Notification.id == notif_id, Notification.user_id == current_user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    return {"ok": True}
