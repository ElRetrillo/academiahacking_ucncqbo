from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_challenge_service,
    get_current_user,
    get_current_user_optional,
)
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


@router.get("", response_model=list[ChallengePublic])
async def list_challenges(
    category: Optional[str] = Query(None, description="Filter by challenge category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: EASY, MEDIUM, HARD, INSANE"),
    challenge_service: ChallengeService = Depends(get_challenge_service),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return await challenge_service.get_public_challenges(user, category=category, difficulty=difficulty)


@router.get("/recent", response_model=list[ChallengePublic])
async def get_recent_challenges(
    limit: int = Query(5, ge=1, le=20),
    challenge_service: ChallengeService = Depends(get_challenge_service),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return await challenge_service.get_recent_challenges(user=user, limit=limit)


@router.get("/categories")
async def get_category_summary(
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    return await challenge_service.get_category_summary()


@router.get("/{challenge_id_or_slug}", response_model=ChallengePublic)
async def get_challenge(
    challenge_id_or_slug: str,
    challenge_service: ChallengeService = Depends(get_challenge_service),
    user: Optional[User] = Depends(get_current_user_optional),
):
    return await challenge_service.get_challenge_by_id_or_slug(challenge_id_or_slug, user)


@router.post(
    "/{challenge_id_or_slug}/submit",
    response_model=FlagSubmissionResponse,
    dependencies=[Depends(rate_limit_flag_submit)],
)
async def submit_flag(
    challenge_id_or_slug: str,
    req: FlagSubmissionRequest,
    current_user: User = Depends(get_current_user),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    return await challenge_service.submit_flag(
        challenge_id_or_slug=challenge_id_or_slug,
        submitted_flag=req.flag,
        user=current_user,
    )


@router.post("/{challenge_id_or_slug}/start", response_model=ChallengeInstanceResponse)
async def start_instance(
    challenge_id_or_slug: str,
    current_user: User = Depends(get_current_user),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    return await challenge_service.start_instance(
        challenge_id_or_slug=challenge_id_or_slug,
        user=current_user,
    )


@router.post("/{challenge_id_or_slug}/stop", response_model=ChallengeInstanceResponse)
async def stop_instance(
    challenge_id_or_slug: str,
    current_user: User = Depends(get_current_user),
    challenge_service: ChallengeService = Depends(get_challenge_service),
):
    return await challenge_service.stop_instance(
        challenge_id_or_slug=challenge_id_or_slug,
        user=current_user,
    )
