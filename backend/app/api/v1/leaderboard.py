from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.leaderboard import LeaderboardResponse, CountryLeaderboardEntry
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Get live player rankings sorted by:
    1. Score (DESC)
    2. Last solve timestamp (ASC, earlier solve wins tiebreaker)
    3. User start date (ASC)
    """
    return await LeaderboardService.get_global_leaderboard(db, limit=limit)


@router.get("/countries", response_model=List[CountryLeaderboardEntry])
async def get_countries_leaderboard(db: AsyncSession = Depends(get_db)):
    """Get aggregated statistics by player nationality."""
    return await LeaderboardService.get_country_leaderboard(db)
