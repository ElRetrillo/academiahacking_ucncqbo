from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, nulls_last

from app.models.user import User
from app.models.solve import Solve
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardResponse, CountryLeaderboardEntry


class LeaderboardService:
    @staticmethod
    async def get_global_leaderboard(db: AsyncSession, limit: int = 100) -> LeaderboardResponse:
        # Subquery to calculate the latest solve timestamp and total solves per user
        solve_stats_subquery = (
            select(
                Solve.user_id,
                func.count(Solve.id).label("solves_count"),
                func.max(Solve.solved_at).label("last_solve_at"),
            )
            .group_by(Solve.user_id)
            .subquery()
        )

        query = (
            select(
                User.id,
                User.username,
                User.nationality,
                User.score,
                User.created_at,
                User.last_connected_at,
                func.coalesce(solve_stats_subquery.c.solves_count, 0).label("solves_count"),
                solve_stats_subquery.c.last_solve_at,
            )
            .outerjoin(solve_stats_subquery, User.id == solve_stats_subquery.c.user_id)
            .where(User.is_active == True, User.role == "user")
            .order_by(
                desc(User.score),
                solve_stats_subquery.c.last_solve_at.asc().nulls_last(),
                User.created_at.asc(),
            )
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        leaderboard_entries: List[LeaderboardEntry] = []
        for idx, row in enumerate(rows, start=1):
            leaderboard_entries.append(
                LeaderboardEntry(
                    rank=idx,
                    user_id=row.id,
                    username=row.username,
                    nationality=row.nationality,
                    score=row.score,
                    solves_count=row.solves_count,
                    start_date=row.created_at,
                    last_connected_at=row.last_connected_at,
                    last_solve_at=row.last_solve_at,
                )
            )

        # Count total active players
        total_query = select(func.count()).select_from(User).where(User.is_active == True, User.role == "user")
        total_res = await db.execute(total_query)
        total_players = total_res.scalar() or 0

        return LeaderboardResponse(total_players=total_players, leaderboard=leaderboard_entries)

    @staticmethod
    async def get_country_leaderboard(db: AsyncSession) -> List[CountryLeaderboardEntry]:
        solve_subquery = (
            select(
                Solve.user_id,
                func.count(Solve.id).label("solves_count"),
            )
            .group_by(Solve.user_id)
            .subquery()
        )

        query = (
            select(
                User.nationality,
                func.count(User.id).label("total_players"),
                func.sum(User.score).label("total_score"),
                func.coalesce(func.sum(solve_subquery.c.solves_count), 0).label("total_solves"),
            )
            .outerjoin(solve_subquery, User.id == solve_subquery.c.user_id)
            .where(User.is_active == True, User.role == "user")
            .group_by(User.nationality)
            .order_by(desc("total_score"), desc("total_solves"))
        )

        result = await db.execute(query)
        rows = result.all()

        return [
            CountryLeaderboardEntry(
                nationality=row.nationality,
                total_players=row.total_players,
                total_score=row.total_score or 0,
                total_solves=row.total_solves,
            )
            for row in rows
        ]
