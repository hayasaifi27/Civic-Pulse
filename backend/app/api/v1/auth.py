from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_tokens,
    get_current_user, require_admin
)
from app.repositories import ProfileRepository
from app.schemas import (
    UserCreate, UserResponse, LoginRequest, Token, RefreshRequest,
    TokenData, UserRole
)
from app.models import Profile
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    repo = ProfileRepository(db)
    
    existing = await repo.get_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    profile = Profile(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=UserRole.CITIZEN,
        is_verified=False
    )
    profile.hashed_password = hashed_password
    
    await repo.create(profile)
    
    return profile


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = ProfileRepository(db)
    user = await repo.get_by_email(credentials.email)
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    tokens = create_tokens(user)
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=3600
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    from app.core.security import decode_token, create_access_token, create_refresh_token
    
    payload = decode_token(request.refresh_token.replace("refresh_", "") if request.refresh_token.startswith("refresh_") else request.refresh_token)
    if not payload or payload.type != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    repo = ProfileRepository(db)
    user = await repo.get_by_id(uuid.UUID(payload.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    tokens = create_tokens(user)
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=3600
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Profile = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    user_data: dict,
    current_user: Profile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ProfileRepository(db)
    allowed_fields = {"full_name", "phone", "avatar_url", "preferences"}
    update_data = {k: v for k, v in user_data.items() if k in allowed_fields}
    updated = await repo.update(current_user.id, update_data)
    return updated


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}