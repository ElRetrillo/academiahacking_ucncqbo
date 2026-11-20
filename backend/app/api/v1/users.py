from fastapi import APIRouter, Depends

from app.api.deps import get_user_service
from app.schemas.user import UserPublicProfileDetail
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{username}/profile", response_model=UserPublicProfileDetail)
async def get_user_profile(
    username: str,
    user_service: UserService = Depends(get_user_service),
):
    """Retrieve public player profile without exposing private PII."""
    return await user_service.get_public_user_profile(username)
