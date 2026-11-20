from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.solve import Solve
from app.models.user import User


class SqlAlchemyUserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: str, active_only: bool = False) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        if active_only:
            query = query.where(User.is_active.is_(True))
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str, active_only: bool = False) -> Optional[User]:
        query = select(User).where(User.username == username)
        if active_only:
            query = query.where(User.is_active.is_(True))
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        normalized = identifier.strip()
        query = select(User).where(
            or_(
                User.username == normalized,
                func.lower(User.email) == normalized.lower(),
            )
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def find_conflicting_user(self, username: str, email: str) -> Optional[User]:
        query = (
            select(User)
            .where(
                or_(
                    func.lower(User.username) == username.strip().lower(),
                    func.lower(User.email) == email.strip().lower(),
                )
            )
            .limit(1)
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        result = await self._db.execute(select(func.count()).select_from(User))
        return int(result.scalar() or 0)

    async def has_any_admin(self) -> bool:
        result = await self._db.execute(select(User.id).where(User.role == "admin").limit(1))
        return result.scalar_one_or_none() is not None

    async def list_all_with_solves_count(self) -> list[tuple[User, int]]:
        solves_subquery = (
            select(Solve.user_id, func.count(Solve.id).label("cnt"))
            .group_by(Solve.user_id)
            .subquery()
        )
        query = (
            select(User, func.coalesce(solves_subquery.c.cnt, 0).label("solves_count"))
            .outerjoin(solves_subquery, User.id == solves_subquery.c.user_id)
            .order_by(desc(User.created_at))
        )
        result = await self._db.execute(query)
        return [(row[0], int(row[1])) for row in result.all()]

    async def get_solves_count(self, user_id: str) -> int:
        result = await self._db.execute(
            select(func.count()).select_from(Solve).where(Solve.user_id == user_id)
        )
        return int(result.scalar() or 0)

    async def get_solves_by_category(self, user_id: str) -> list[tuple[str, int]]:
        result = await self._db.execute(
            select(Challenge.category, func.count(Solve.id).label("count"))
            .join(Solve, Solve.challenge_id == Challenge.id)
            .where(Solve.user_id == user_id)
            .group_by(Challenge.category)
        )
        return [(str(row.category), int(row.count)) for row in result.all()]

    async def get_recent_solves(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[tuple[str, str, str, int, datetime]]:
        result = await self._db.execute(
            select(
                Challenge.title,
                Challenge.category,
                Challenge.difficulty,
                Solve.points_awarded,
                Solve.solved_at,
            )
            .join(Solve, Solve.challenge_id == Challenge.id)
            .where(Solve.user_id == user_id)
            .order_by(Solve.solved_at.desc())
            .limit(limit)
        )
        return [
            (str(row.title), str(row.category), str(row.difficulty), int(row.points_awarded), row.solved_at)
            for row in result.all()
        ]

    async def get_ordered_solves(self, user_id: str) -> list[tuple[str, datetime]]:
        result = await self._db.execute(
            select(Solve.challenge_id, Solve.solved_at)
            .where(Solve.user_id == user_id)
            .order_by(Solve.solved_at.asc())
        )
        return [(str(row.challenge_id), row.solved_at) for row in result.all()]

    async def create(self, user: User) -> User:
        self._db.add(user)
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
        await self._db.refresh(user)
        return user

    async def save(self, user: User) -> User:
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
        await self._db.refresh(user)
        return user

    async def touch_last_connected(self, user: User, now: datetime) -> None:
        user.last_connected_at = now
        await self._db.commit()
