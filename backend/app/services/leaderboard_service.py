from app.repositories.protocols import LeaderboardRepositoryProtocol
from app.schemas.leaderboard import CountryLeaderboardEntry, LeaderboardResponse


class LeaderboardService:
    def __init__(self, leaderboard_repo: LeaderboardRepositoryProtocol) -> None:
        self._leaderboard_repo = leaderboard_repo

    async def get_global_leaderboard(self, limit: int = 100) -> LeaderboardResponse:
        entries = await self._leaderboard_repo.get_global_entries(limit=limit)
        total_players = await self._leaderboard_repo.count_active_players()
        return LeaderboardResponse(total_players=total_players, leaderboard=entries)

    async def get_country_leaderboard(self) -> list[CountryLeaderboardEntry]:
        return await self._leaderboard_repo.get_country_entries()
