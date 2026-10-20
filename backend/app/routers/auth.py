"""
CareerCompass – Authentication router.
Endpoints: POST /register, POST /login, GET /me, DELETE /me (account deletion FR-20)
Rate limited on register and login (NFR security).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.models import User, StudentProfile, AuditLog
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """
    Register a new user account (FR-1, FR-2).
    - Unique email enforced at DB level.
    - Password must be ≥ 8 characters (enforced by Pydantic schema).
    - Exactly one role per account.
    """
    # Check for existing email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.flush()  # get user.id before creating profile

    # Create student profile automatically for students
    if body.role == "student":
        profile = StudentProfile(user_id=user.id)
        db.add(profile)

    # Audit log
    audit = AuditLog(action="user_registered", resource_type="user", resource_id=user.id)
    db.add(audit)

    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Login with email/password; returns a 30-minute JWT access token (NFR-2).
    Rate-limited to prevent brute-force attacks.
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user's profile."""
    return UserOut.model_validate(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Hard-delete all of the student's personal and assessment data (FR-20).
    Cascade deletes handle all related tables via FK ON DELETE CASCADE.
    Non-student roles also deleted but cascade scope is smaller.
    """
    audit = AuditLog(
        action="account_deleted",
        resource_type="user",
        resource_id=current_user.id,
        detail={"email": current_user.email, "role": current_user.role},
    )
    db.add(audit)

    user = await db.get(User, current_user.id)
    await db.delete(user)
    await db.commit()
