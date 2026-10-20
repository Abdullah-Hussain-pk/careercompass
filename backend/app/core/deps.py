"""
CareerCompass – FastAPI dependency injection for auth & RBAC.

Every protected route must use one of these dependencies.
Ownership checks (student can only access own data) are also here.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode JWT, verify token validity, and return the User ORM object.
    Raises 401 on invalid/expired tokens.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


async def get_current_active_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """RBAC: must be a student."""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


async def get_current_counsellor(
    current_user: User = Depends(get_current_user),
) -> User:
    """RBAC: must be a counsellor."""
    if current_user.role != "counsellor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Counsellor access required",
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """RBAC: must be an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_expert(
    current_user: User = Depends(get_current_user),
) -> User:
    """RBAC: must be an industry expert."""
    if current_user.role != "expert":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Expert access required",
        )
    return current_user


async def get_current_admin_or_expert(
    current_user: User = Depends(get_current_user),
) -> User:
    """RBAC: admin OR expert (for submission listing)."""
    if current_user.role not in ("admin", "expert"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Expert access required",
        )
    return current_user


def require_owner_or_admin(resource_user_id: str, current_user: User) -> None:
    """
    Ownership check: raises 403 if the caller is not the resource owner
    and not an admin. Use this in route handlers that serve student-specific data.
    """
    if current_user.role == "admin":
        return
    if current_user.id != resource_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only access your own data",
        )
