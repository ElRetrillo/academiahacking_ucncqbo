from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    nationality: str
    score: int
    solves_count: int
    start_date: datetime  # User registration date
    last_connected_at: datetime  # Last active telemetry
    last_solve_at: Optional[datetime] = None


class CountryLeaderboardEntry(BaseModel):
    nationality: str
    total_players: int
    total_score: int
    total_solves: int


class LeaderboardResponse(BaseModel):
    total_players: int
    leaderboard: List[LeaderboardEntry]
