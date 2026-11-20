from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional
from app.database import get_db
from app.models.user import User
from app.schemas.challenge import (
    ChallengeInstanceResponse,
    ChallengePublic,
    FlagSubmissionRequest,
    FlagSubmissionResponse,
)
from app.services.challenge_service import ChallengeService
from app.services.rate_limiter import rate_limit_flag_submit

router = APIRouter(prefix="/challenges", tags=["Challenges"])


@router.get("", response_model=List[ChallengePublic])
async def list_challenges(
    category: Optional[str] = Query(None, description="Filter by challenge category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: EASY, MEDIUM, HARD, INSANE"),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return await ChallengeService.get_public_challenges(db, user, category=category, difficulty=difficulty)


@router.get("/recent", response_model=List[ChallengePublic])
async def get_recent_challenges(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return await ChallengeService.get_recent_challenges(db, user=user, limit=limit)


@router.get("/categories")
async def get_category_summary(db: AsyncSession = Depends(get_db)):
    return await ChallengeService.get_category_summary(db)


@router.get("/{challenge_id_or_slug}", response_model=ChallengePublic)
async def get_challenge(
    challenge_id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return await ChallengeService.get_challenge_by_id_or_slug(db, challenge_id_or_slug, user)


@router.post(
    "/{challenge_id_or_slug}/submit",
    response_model=FlagSubmissionResponse,
    dependencies=[Depends(rate_limit_flag_submit)],
)
async def submit_flag(
    challenge_id_or_slug: str,
    req: FlagSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChallengeService.submit_flag(
        db=db,
        challenge_id_or_slug=challenge_id_or_slug,
        submitted_flag=req.flag,
        user=current_user,
    )


@router.post("/{challenge_id_or_slug}/start", response_model=ChallengeInstanceResponse)
async def start_instance(
    challenge_id_or_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChallengeService.start_instance(
        db=db, challenge_id_or_slug=challenge_id_or_slug, user=current_user
    )


@router.post("/{challenge_id_or_slug}/stop", response_model=ChallengeInstanceResponse)
async def stop_instance(
    challenge_id_or_slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChallengeService.stop_instance(
        db=db, challenge_id_or_slug=challenge_id_or_slug, user=current_user
    )
