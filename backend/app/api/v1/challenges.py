from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
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
    category: Optional[str] = Query(None, description="Filter by challenge category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: EASY, MEDIUM, HARD, INSANE"),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List all active challenges with optional filtering by category and difficulty.
    If authenticated, includes `is_solved` status for the current player.
    """
    return await ChallengeService.get_public_challenges(db, user, category=category, difficulty=difficulty)


@router.get("/recent", response_model=List[ChallengePublic])
async def get_recent_challenges(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get top recently added CTF challenges for the scoreboard feed."""
    return await ChallengeService.get_recent_challenges(db, user=user, limit=limit)


@router.get("/categories")
async def get_category_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get active CTF categories and available challenge counts."""
    return await ChallengeService.get_category_summary(db)


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
