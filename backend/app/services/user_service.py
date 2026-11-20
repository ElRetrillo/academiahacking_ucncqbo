from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.protocols import LeaderboardRepositoryProtocol, UserRepositoryProtocol
from app.schemas.user import (
    RecentSolveDetail,
    UserAdminUpdate,
    UserProfile,
    UserProfileDetail,
    UserProfileSolvesBreakdown,
    UserPublicProfileDetail,
)

_RANK_THRESHOLDS = (
    (1, "Noob"),
    (500, "Script Kiddie"),
    (1000, "Hacker"),
    (2000, "Pro Hacker"),
    (4000, "Elite Hacker"),
    (8000, "Guru"),
)


def _to_user_profile(user: User, solves_count: int) -> UserProfile:
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        nationality=user.nationality,
        role=user.role,
        score=user.score,
        created_at=user.created_at,
        last_connected_at=user.last_connected_at,
        is_active=user.is_active,
        solves_count=solves_count,
    )


class UserService:
    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        leaderboard_repo: LeaderboardRepositoryProtocol,
    ) -> None:
        self._user_repo = user_repo
        self._leaderboard_repo = leaderboard_repo

    @staticmethod
    def get_rank_name(score: int) -> str:
        for threshold, name in _RANK_THRESHOLDS:
            if score < threshold:
                return name
        return "Omniscient"

    async def _compute_profile_metrics(self, username: str) -> tuple[User, dict]:
        user = await self._user_repo.get_by_username(username, active_only=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        solves_count = await self._user_repo.get_solves_count(user.id)
        global_rank = await self._leaderboard_repo.get_user_global_rank(user)
        rank_name = self.get_rank_name(user.score)

        category_rows = await self._user_repo.get_solves_by_category(user.id)
        solves_by_category = [
            UserProfileSolvesBreakdown(category=category, count=count)
            for category, count in category_rows
        ]

        recent_rows = await self._user_repo.get_recent_solves(user.id, limit=10)
        recent_solves = [
            RecentSolveDetail(
                challenge_title=title,
                category=category,
                difficulty=difficulty,
                points_awarded=points_awarded,
                solved_at=solved_at,
            )
            for title, category, difficulty, points_awarded, solved_at in recent_rows
        ]

        metrics = {
            "id": user.id,
            "username": user.username,
            "nationality": user.nationality,
            "score": user.score,
            "global_rank": global_rank,
            "rank_name": rank_name,
            "created_at": user.created_at,
            "solves_count": solves_count,
            "solves_by_category": solves_by_category,
            "recent_solves": recent_solves,
        }
        return user, metrics

    async def get_public_user_profile(self, username: str) -> UserPublicProfileDetail:
        _, metrics = await self._compute_profile_metrics(username)
        return UserPublicProfileDetail(**metrics)

    async def get_user_profile_detail(self, username: str) -> UserProfileDetail:
        user, metrics = await self._compute_profile_metrics(username)
        return UserProfileDetail(
            **metrics,
            email=user.email,
            role=user.role,
            last_connected_at=user.last_connected_at,
            is_active=user.is_active,
        )

    async def admin_list_users(self) -> list[UserProfile]:
        rows = await self._user_repo.list_all_with_solves_count()
        return [_to_user_profile(user, solves_count) for user, solves_count in rows]

    async def admin_update_user(
        self,
        user_id: str,
        req: UserAdminUpdate,
        acting_admin: User,
    ) -> UserProfile:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.id == acting_admin.id:
            if req.is_active is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Administrators cannot deactivate their own account.",
                )
            if req.role is not None and req.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Administrators cannot downgrade their own role.",
                )

        if req.role is not None:
            user.role = req.role
        if req.is_active is not None:
            user.is_active = req.is_active
        if req.nationality is not None:
            user.nationality = req.nationality
        if req.score is not None:
            user.score = req.score

        updated_user = await self._user_repo.save(user)
        solves_count = await self._user_repo.get_solves_count(updated_user.id)
        return _to_user_profile(updated_user, solves_count)
