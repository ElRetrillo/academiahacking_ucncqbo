from datetime import datetime
from typing import Union

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.solve import Solve
from app.models.user import User
from app.schemas.leaderboard import CountryLeaderboardEntry, LeaderboardEntry


class SqlAlchemyLeaderboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_global_entries(self, limit: int = 100) -> list[LeaderboardEntry]:
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
            .where(User.is_active.is_(True), User.role == "user")
            .order_by(
                desc(User.score),
                solve_stats_subquery.c.last_solve_at.asc().nulls_last(),
                User.created_at.asc(),
                User.id.asc(),
            )
            .limit(limit)
        )

        result = await self._db.execute(query)
        rows = result.all()

        return [
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
            for idx, row in enumerate(rows, start=1)
        ]

    async def count_active_players(self) -> int:
        total_res = await self._db.execute(
            select(func.count())
            .select_from(User)
            .where(User.is_active.is_(True), User.role == "user")
        )
        return total_res.scalar() or 0

    async def get_country_entries(self) -> list[CountryLeaderboardEntry]:
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
            .where(User.is_active.is_(True), User.role == "user")
            .group_by(User.nationality)
            .order_by(desc("total_score"), desc("total_solves"))
        )

        result = await self._db.execute(query)
        return [
            CountryLeaderboardEntry(
                nationality=row.nationality,
                total_players=row.total_players,
                total_score=row.total_score or 0,
                total_solves=row.total_solves,
            )
            for row in result.all()
        ]

    async def get_user_global_rank(self, user: User) -> Union[int, str]:
        if user.role != "user" or not user.is_active or user.score <= 0:
            return "Sin clasificar"

        user_solve_res = await self._db.execute(
            select(
                func.count(Solve.id).label("cnt"),
                func.max(Solve.solved_at).label("last_solve_at"),
            ).where(Solve.user_id == user.id)
        )
        solve_row = user_solve_res.one()
        if int(solve_row.cnt or 0) == 0 or solve_row.last_solve_at is None:
            return "Sin clasificar"

        target_last_solve = solve_row.last_solve_at
        if isinstance(target_last_solve, str):
            target_last_solve = datetime.fromisoformat(target_last_solve)

        solve_stats_subquery = (
            select(
                Solve.user_id,
                func.max(Solve.solved_at).label("last_solve_at"),
            )
            .group_by(Solve.user_id)
            .subquery()
        )

        ahead_condition = (
            (User.score > user.score)
            | ((User.score == user.score) & (solve_stats_subquery.c.last_solve_at < target_last_solve))
            | (
                (User.score == user.score)
                & (solve_stats_subquery.c.last_solve_at == target_last_solve)
                & (User.created_at < user.created_at)
            )
            | (
                (User.score == user.score)
                & (solve_stats_subquery.c.last_solve_at == target_last_solve)
                & (User.created_at == user.created_at)
                & (User.id < user.id)
            )
        )

        ahead_query = (
            select(func.count(User.id))
            .join(solve_stats_subquery, User.id == solve_stats_subquery.c.user_id)
            .where(
                User.is_active.is_(True),
                User.role == "user",
                User.score > 0,
                ahead_condition,
            )
        )
        ahead_res = await self._db.execute(ahead_query)
        ahead_count = ahead_res.scalar() or 0
        return ahead_count + 1
