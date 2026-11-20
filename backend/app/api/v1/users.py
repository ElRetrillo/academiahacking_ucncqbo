from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserPublicProfileDetail
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{username}/profile", response_model=UserPublicProfileDetail)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve public player profile without exposing private PII."""
    return await UserService.get_public_user_profile(db, username)
