from typing import Union
from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.solve import Solve
from app.models.user import User
from app.schemas.user import (
    RecentSolveDetail,
    UserProfileDetail,
    UserProfileSolvesBreakdown,
    UserPublicProfileDetail,
)


class UserService:
    @staticmethod
    def get_rank_name(score: int) -> str:
        if score == 0:
            return "Noob"
        elif score < 500:
            return "Script Kiddie"
        elif score < 1000:
            return "Hacker"
        elif score < 2000:
            return "Pro Hacker"
        elif score < 4000:
            return "Elite Hacker"
        elif score < 8000:
            return "Guru"
        else:
            return "Omniscient"

    @staticmethod
    async def _compute_profile_metrics(db: AsyncSession, username: str) -> tuple[User, dict]:
        result = await db.execute(
            select(User).where(User.username == username, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        solves_count_res = await db.execute(
            select(func.count()).select_from(Solve).where(Solve.user_id == user.id)
        )
        solves_count = solves_count_res.scalar() or 0

        global_rank: Union[int, str] = "Sin clasificar"
        if user.role == "user" and user.score > 0 and solves_count > 0:
            active_solvers_subquery = select(Solve.user_id).group_by(Solve.user_id).subquery()
            rank_query = (
                select(User.id)
                .join(active_solvers_subquery, User.id == active_solvers_subquery.c.user_id)
                .where(User.is_active == True, User.role == "user", User.score > 0)
                .order_by(desc(User.score), User.created_at.asc())
            )
            rank_res = await db.execute(rank_query)
            ranked_user_ids = [row[0] for row in rank_res.all()]
            if user.id in ranked_user_ids:
                global_rank = ranked_user_ids.index(user.id) + 1

        rank_name = UserService.get_rank_name(user.score)

        solves_by_category_res = await db.execute(
            select(Challenge.category, func.count(Solve.id).label("count"))
            .join(Solve, Solve.challenge_id == Challenge.id)
            .where(Solve.user_id == user.id)
            .group_by(Challenge.category)
        )
        solves_by_category = [
            UserProfileSolvesBreakdown(category=row.category, count=row.count)
            for row in solves_by_category_res.all()
        ]

        recent_solves_res = await db.execute(
            select(
                Challenge.title,
                Challenge.category,
                Challenge.difficulty,
                Solve.points_awarded,
                Solve.solved_at,
            )
            .join(Solve, Solve.challenge_id == Challenge.id)
            .where(Solve.user_id == user.id)
            .order_by(Solve.solved_at.desc())
            .limit(10)
        )
        recent_solves = [
            RecentSolveDetail(
                challenge_title=row.title,
                challengeTitle=row.title,
                category=row.category,
                difficulty=row.difficulty,
                points_awarded=row.points_awarded,
                pointsAwarded=row.points_awarded,
                solved_at=row.solved_at,
                solvedAt=row.solved_at,
            )
            for row in recent_solves_res.all()
        ]

        metrics = {
            "id": user.id,
            "username": user.username,
            "nationality": user.nationality,
            "score": user.score,
            "global_rank": global_rank,
            "globalRank": global_rank,
            "rank_name": rank_name,
            "rankName": rank_name,
            "created_at": user.created_at,
            "createdAt": user.created_at,
            "solves_count": solves_count,
            "solvesCount": solves_count,
            "solves_by_category": solves_by_category,
            "solvesByCategory": solves_by_category,
            "recent_solves": recent_solves,
            "recentSolves": recent_solves,
        }
        return user, metrics

    @staticmethod
    async def get_public_user_profile(db: AsyncSession, username: str) -> UserPublicProfileDetail:
        _, metrics = await UserService._compute_profile_metrics(db, username)
        return UserPublicProfileDetail(**metrics)

    @staticmethod
    async def get_user_profile_detail(db: AsyncSession, username: str) -> UserProfileDetail:
        user, metrics = await UserService._compute_profile_metrics(db, username)
        return UserProfileDetail(
            **metrics,
            email=user.email,
            role=user.role,
            last_connected_at=user.last_connected_at,
            lastConnectedAt=user.last_connected_at,
            is_active=user.is_active,
            isActive=user.is_active,
        )
