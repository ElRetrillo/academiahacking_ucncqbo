from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.solve import Solve
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserProfile, UserUpdate
from app.services.security import hash_password, verify_password, create_access_token


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, req: RegisterRequest) -> User:
        # Check if username or email already exists
        query = select(User).where(or_(User.username == req.username, User.email == req.email))
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.username == req.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already registered."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered."
            )

        # Assign "admin" to the first user, and "user" to everyone else
        count_query = select(func.count()).select_from(User)
        count_res = await db.execute(count_query)
        user_count = count_res.scalar() or 0
        role = "admin" if user_count == 0 else "user"

        new_user = User(
            username=req.username,
            email=req.email,
            hashed_password=hash_password(req.password),
            nationality=req.nationality.upper(),
            role=role,
            score=0,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            last_connected_at=datetime.now(timezone.utc),
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, req: LoginRequest) -> TokenResponse:
        query = select(User).where(
            or_(User.username == req.username_or_email, User.email == req.username_or_email)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )

        # Update last connected timestamp
        user.last_connected_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)

        # Get solves count
        solves_count_query = select(func.count()).select_from(Solve).where(Solve.user_id == user.id)
        solves_res = await db.execute(solves_count_query)
        solves_count = solves_res.scalar() or 0

        user_profile = UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            nationality=user.nationality,
            role=user.role,
            score=user.score,
            created_at=user.created_at,
            last_connected_at=user.last_connected_at,
            is_active=user.is_active,
            solves_count=solves_count,
        )

        access_token = create_access_token(subject=user.id)
        return TokenResponse(access_token=access_token, user=user_profile)

    @staticmethod
    async def get_user_profile(db: AsyncSession, user: User) -> UserProfile:
        solves_count_query = select(func.count()).select_from(Solve).where(Solve.user_id == user.id)
        solves_res = await db.execute(solves_count_query)
        solves_count = solves_res.scalar() or 0

        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            nationality=user.nationality,
            role=user.role,
            score=user.score,
            created_at=user.created_at,
            last_connected_at=user.last_connected_at,
            is_active=user.is_active,
            solves_count=solves_count,
        )

    @staticmethod
    async def update_profile(db: AsyncSession, user: User, req: UserUpdate) -> UserProfile:
        if req.nationality:
            user.nationality = req.nationality.upper()

        if req.new_password:
            if not req.current_password or not verify_password(req.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password does not match."
                )
            user.hashed_password = hash_password(req.new_password)

        await db.commit()
        await db.refresh(user)
        return await AuthService.get_user_profile(db, user)
