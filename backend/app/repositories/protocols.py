from datetime import datetime
from typing import Optional, Protocol, Union

from app.models.challenge import Challenge
from app.models.instance import ChallengeInstance
from app.models.user import User
from app.schemas.leaderboard import CountryLeaderboardEntry, LeaderboardEntry


class UserRepositoryProtocol(Protocol):
    async def get_by_id(self, user_id: str, active_only: bool = False) -> Optional[User]:
        ...

    async def get_by_username(self, username: str, active_only: bool = False) -> Optional[User]:
        ...

    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        ...

    async def find_conflicting_user(self, username: str, email: str) -> Optional[User]:
        ...

    async def count_all(self) -> int:
        ...

    async def has_any_admin(self) -> bool:
        ...

    async def list_all_with_solves_count(self) -> list[tuple[User, int]]:
        ...

    async def get_solves_count(self, user_id: str) -> int:
        ...

    async def get_solves_by_category(self, user_id: str) -> list[tuple[str, int]]:
        ...

    async def get_recent_solves(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[tuple[str, str, str, int, datetime]]:
        ...

    async def get_ordered_solves(self, user_id: str) -> list[tuple[str, datetime]]:
        ...

    async def create(self, user: User) -> User:
        ...

    async def save(self, user: User) -> User:
        ...

    async def touch_last_connected(self, user: User, now: datetime) -> None:
        ...


class ChallengeRepositoryProtocol(Protocol):
    async def list_active(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> list[Challenge]:
        ...

    async def list_recent_active(self, limit: int = 5) -> list[Challenge]:
        ...

    async def get_category_summary(self) -> list[tuple[str, int]]:
        ...

    async def get_active_by_id_or_slug(self, challenge_id_or_slug: str) -> Optional[Challenge]:
        ...

    async def get_by_id(self, challenge_id: str) -> Optional[Challenge]:
        ...

    async def get_by_slug(self, slug: str) -> Optional[Challenge]:
        ...

    async def list_all(self) -> list[Challenge]:
        ...

    async def count_active(self) -> int:
        ...

    async def get_solved_challenge_ids(self, user_id: str) -> set[str]:
        ...

    async def has_user_solved(self, user_id: str, challenge_id: str) -> bool:
        ...

    async def record_incorrect_submission(
        self,
        user_id: str,
        challenge_id: str,
        flag_hash: str,
        now: datetime,
    ) -> None:
        ...

    async def record_correct_solve(
        self,
        user: User,
        challenge: Challenge,
        flag_hash: str,
        now: datetime,
    ) -> tuple[bool, int]:
        ...

    async def get_running_instance(
        self,
        user_id: str,
        challenge_id: str,
    ) -> Optional[ChallengeInstance]:
        ...

    async def create_instance(
        self,
        user_id: str,
        challenge_id: str,
        now: datetime,
    ) -> ChallengeInstance:
        ...

    async def stop_instance(
        self,
        instance: ChallengeInstance,
        now: datetime,
    ) -> ChallengeInstance:
        ...

    async def create(self, challenge: Challenge) -> Challenge:
        ...

    async def save(self, challenge: Challenge) -> Challenge:
        ...

    async def delete(self, challenge: Challenge) -> None:
        ...


class LeaderboardRepositoryProtocol(Protocol):
    async def get_global_entries(self, limit: int = 100) -> list[LeaderboardEntry]:
        ...

    async def count_active_players(self) -> int:
        ...

    async def get_country_entries(self) -> list[CountryLeaderboardEntry]:
        ...

    async def get_user_global_rank(self, user: User) -> Union[int, str]:
        ...


class TokenRevocationRepositoryProtocol(Protocol):
    async def is_revoked(self, jti: str) -> bool:
        ...

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        ...
