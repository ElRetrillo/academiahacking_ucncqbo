from fastapi import APIRouter, Depends, status

from app.api.deps import get_challenge_service, get_current_admin, get_user_service
from app.models.user import User
from app.schemas.challenge import ChallengeAdmin, ChallengeCreate, ChallengeUpdate
from app.schemas.user import UserAdminUpdate, UserProfile
from app.services.challenge_service import ChallengeService
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.get("/challenges", response_model=list[ChallengeAdmin])
async def admin_list_challenges(
    admin: User = Depends(get_current_admin),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    """List all challenges with internal metadata (flags redacted)."""
    return await challenge_service.admin_get_all_challenges()


@router.post("/challenges", response_model=ChallengeAdmin, status_code=status.HTTP_201_CREATED)
async def admin_create_challenge(
    req: ChallengeCreate,
    admin: User = Depends(get_current_admin),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    """Create a new CTF challenge with difficulty, points, and flag."""
    return await challenge_service.admin_create_challenge(req)


@router.put("/challenges/{challenge_id}", response_model=ChallengeAdmin)
async def admin_update_challenge(
    challenge_id: str,
    req: ChallengeUpdate,
    admin: User = Depends(get_current_admin),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    """Update challenge details, points, difficulty, or flag."""
    return await challenge_service.admin_update_challenge(challenge_id, req)


@router.delete("/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_challenge(
    challenge_id: str,
    admin: User = Depends(get_current_admin),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    """Remove a challenge."""
    await challenge_service.admin_delete_challenge(challenge_id)


@router.get("/users", response_model=list[UserProfile])
async def admin_list_users(
    admin: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    """List all registered users, roles, points, nationality, and activity timestamps."""
    return await user_service.admin_list_users()


@router.put("/users/{user_id}", response_model=UserProfile)
async def admin_update_user(
    user_id: str,
    req: UserAdminUpdate,
    admin: User = Depends(get_current_admin),
    user_service: UserService = Depends(get_user_service),
):
    """Update user role, activation status, nationality, or score."""
    return await user_service.admin_update_user(user_id, req, acting_admin=admin)
