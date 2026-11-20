from fastapi import APIRouter, Depends, Query

from app.api.deps import get_leaderboard_service
from app.schemas.leaderboard import CountryLeaderboardEntry, LeaderboardResponse
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(default=100, ge=1, le=500),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get live player rankings sorted by score, earliest last solve time, and registration date."""
    return await leaderboard_service.get_global_leaderboard(limit=limit)


@router.get("/countries", response_model=list[CountryLeaderboardEntry])
async def get_countries_leaderboard(
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Get aggregated statistics by player nationality."""
    return await leaderboard_service.get_country_leaderboard()
