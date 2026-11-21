from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.models.user import User
from app.repositories.protocols import UserRepositoryProtocol
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserProfile, UserUpdate
from app.services.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepositoryProtocol) -> None:
        self._user_repo = user_repo

    async def register_user(self, req: RegisterRequest) -> User:
        existing_user = await self._user_repo.find_conflicting_user(req.username, req.email)
        if existing_user:
            if existing_user.username.lower() == req.username.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already registered.",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered.",
            )

        role = "user"
        if settings.ALLOW_FIRST_USER_ADMIN and await self._user_repo.count_all() == 0:
            role = "admin"

        now = datetime.now(timezone.utc)
        new_user = User(
            username=req.username,
            email=req.email.lower(),
            hashed_password=hash_password(req.password),
            nationality=req.nationality.upper(),
            role=role,
            score=0,
            is_active=True,
            created_at=now,
            last_connected_at=now,
        )
        try:
            return await self._user_repo.create(new_user)
        except IntegrityError as exc:
            conflict = await self._user_repo.find_conflicting_user(req.username, req.email)
            if conflict and conflict.username.lower() == req.username.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already registered.",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered.",
            ) from exc

    async def authenticate_user(
        self,
        req: LoginRequest,
        token_type: str = "cli",
    ) -> TokenResponse:
        user = await self._user_repo.get_by_username_or_email(req.username_or_email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        await self._user_repo.touch_last_connected(user, datetime.now(timezone.utc))
        user_profile = await self.get_user_profile(user)
        access_token = create_access_token(subject=user.id, token_type=token_type)
        return TokenResponse(access_token=access_token, user=user_profile)

    async def get_user_profile(self, user: User) -> UserProfile:
        solves_count = await self._user_repo.get_solves_count(user.id)
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

    async def update_profile(self, user: User, req: UserUpdate) -> UserProfile:
        if req.nationality:
            user.nationality = req.nationality.upper()

        if req.new_password:
            if not req.current_password or not verify_password(req.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password does not match.",
                )
            user.hashed_password = hash_password(req.new_password)

        updated_user = await self._user_repo.save(user)
        return await self.get_user_profile(updated_user)
