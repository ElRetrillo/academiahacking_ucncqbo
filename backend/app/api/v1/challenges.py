from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.challenge import (
    ChallengePublic,
    FlagSubmissionRequest,
    FlagSubmissionResponse,
)
from app.services.challenge_service import ChallengeService
from app.api.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/challenges", tags=["Challenges"])


@router.get("", response_model=List[ChallengePublic])
async def list_challenges(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List all active challenges.
    If authenticated, includes `is_solved` status for the current player.
    """
    return await ChallengeService.get_public_challenges(db, user)


@router.get("/{challenge_id_or_slug}", response_model=ChallengePublic)
async def get_challenge(
    challenge_id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get challenge details by ID or slug."""
    return await ChallengeService.get_challenge_by_id_or_slug(db, challenge_id_or_slug, user)


@router.post("/{challenge_id_or_slug}/submit", response_model=FlagSubmissionResponse)
async def submit_flag(
    challenge_id_or_slug: str,
    req: FlagSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a flag for validation.
    Performs constant-time verification, awards points, and updates user/leaderboard standings.
    """
    return await ChallengeService.submit_flag(
        db=db,
        challenge_id_or_slug=challenge_id_or_slug,
        submitted_flag=req.flag,
        user=current_user,
    )
