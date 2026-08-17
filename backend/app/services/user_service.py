from datetime import datetime
from typing import Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.user import User
from app.models.solve import Solve
from app.models.challenge import Challenge
from app.schemas.user import UserProfileDetail, UserProfileSolvesBreakdown, RecentSolveDetail


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
    async def get_user_profile_detail(db: AsyncSession, username: str) -> UserProfileDetail:
        # 1. Fetch the user
        query = select(User).where(User.username == username, User.is_active == True)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )

        # Count solves
        solves_count_query = select(func.count()).select_from(Solve).where(Solve.user_id == user.id)
        solves_count_res = await db.execute(solves_count_query)
        solves_count = solves_count_res.scalar() or 0

        # 2. Compute Global Leaderboard Rank: "Sin clasificar" if 0 pts or 0 solves or admin
        global_rank: Union[int, str] = "Sin clasificar"
        if user.role == "user" and user.score > 0 and solves_count > 0:
            active_solvers_subquery = (
                select(Solve.user_id)
                .group_by(Solve.user_id)
                .subquery()
            )
            
            rank_query = (
                select(User.id)
                .join(active_solvers_subquery, User.id == active_solvers_subquery.c.user_id)
                .where(User.is_active == True, User.role == "user", User.score > 0)
                .order_by(desc(User.score), User.created_at.asc())
            )
            
            rank_res = await db.execute(rank_query)
            ranked_user_ids = [row[0] for row in rank_res.all()]
            try:
                global_rank = ranked_user_ids.index(user.id) + 1
            except ValueError:
                global_rank = "Sin clasificar"

        # 3. Get HTB Rank Name Title
        rank_name = UserService.get_rank_name(user.score)

        # 5. Solves breakdown by category
        solves_by_category_query = (
            select(Challenge.category, func.count(Solve.id).label("count"))
            .join(Solve, Solve.challenge_id == Challenge.id)
            .where(Solve.user_id == user.id)
            .group_by(Challenge.category)
        )
        solves_by_category_res = await db.execute(solves_by_category_query)
        solves_by_category = [
            UserProfileSolvesBreakdown(category=row.category, count=row.count)
            for row in solves_by_category_res.all()
        ]

        # 6. Recent solves list (limit to 10)
        recent_solves_query = (
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
        recent_solves_res = await db.execute(recent_solves_query)
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

        return UserProfileDetail(
            id=user.id,
            username=user.username,
            email=user.email,
            nationality=user.nationality,
            role=user.role,
            score=user.score,
            global_rank=global_rank,
            globalRank=global_rank,
            rank_name=rank_name,
            rankName=rank_name,
            created_at=user.created_at,
            createdAt=user.created_at,
            last_connected_at=user.last_connected_at,
            lastConnectedAt=user.last_connected_at,
            is_active=user.is_active,
            isActive=user.is_active,
            solves_count=solves_count,
            solvesCount=solves_count,
            solves_by_category=solves_by_category,
            solvesByCategory=solves_by_category,
            recent_solves=recent_solves,
            recentSolves=recent_solves,
        )
