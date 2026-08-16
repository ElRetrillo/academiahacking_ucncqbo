from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserProfile, UserUpdate, UserProfileDetail
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new player account."""
    user = await AuthService.register_user(db, req)
    return await AuthService.get_user_profile(db, user)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and obtain JWT access token."""
    return await AuthService.authenticate_user(db, req)


@router.get("/me", response_model=UserProfileDetail)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the authenticated player profile and live statistics."""
    return await UserService.get_user_profile_detail(db, current_user.username)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile details such as nationality or password."""
    return await AuthService.update_profile(db, current_user, req)
