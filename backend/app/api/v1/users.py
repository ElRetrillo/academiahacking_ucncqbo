from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserProfileDetail
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{username}/profile", response_model=UserProfileDetail)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve public HTB-style user profile with statistics, leaderboard rank, and recent solves."""
    return await UserService.get_user_profile_detail(db, username)
