"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from app.models.user import User
from app.models.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    AccessibilityPreferences
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register user baru

    Args:
        user_data: Data user untuk registrasi

    Returns:
        TokenResponse dengan access token dan user info
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)

    accessibility_prefs = user_data.accessibility_preferences
    if accessibility_prefs is None:
        accessibility_prefs = AccessibilityPreferences()

    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        role=user_data.role,
        accessibility_preferences=accessibility_prefs.model_dump()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role.value,
            "name": new_user.name
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            role=new_user.role,
            accessibility_preferences=AccessibilityPreferences(**new_user.accessibility_preferences),
            created_at=new_user.created_at
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user

    Args:
        credentials: Email dan password

    Returns:
        TokenResponse dengan access token dan user info
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "name": user.name
        }
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            accessibility_preferences=AccessibilityPreferences(**user.accessibility_preferences),
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user info

    Returns:
        UserResponse dengan info user saat ini
    """
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tidak ditemukan"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        accessibility_preferences=AccessibilityPreferences(**user.accessibility_preferences),
        created_at=user.created_at
    )


@router.patch("/me/accessibility", response_model=UserResponse)
async def update_accessibility_preferences(
    preferences: AccessibilityPreferences,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update accessibility preferences untuk user saat ini

    Args:
        preferences: Preferensi aksesibilitas baru

    Returns:
        UserResponse dengan preferensi yang sudah diupdate
    """
    result = await db.execute(select(User).where(User.id == current_user["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tidak ditemukan"
        )

    user.accessibility_preferences = preferences.model_dump()
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        accessibility_preferences=preferences,
        created_at=user.created_at
    )
