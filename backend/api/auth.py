from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from models.user import User
from schemas.user import UserRegister, UserLogin, TokenResponse
from core.auth import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email==payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(status_code=409, detail="Email already registered")
    else:
        hashed_password = hash_password(payload.password)
        new_user = User(email=payload.email, password_hash=hashed_password, is_active = True, created_at = datetime.now(timezone.utc))
        db.add(new_user)
        await db.commit()
        return {"message":"User Registered"}
        
@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if verify_password(payload.password, user.password_hash):
        access_token = create_access_token({"sub":payload.email})
        return TokenResponse(access_token=access_token)
    




