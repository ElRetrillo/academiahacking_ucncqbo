from typing import Optional

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.models.user import User
from app.repositories.protocols import (
    ChallengeRepositoryProtocol,
    LeaderboardRepositoryProtocol,
    UserRepositoryProtocol,
)
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.challenge import FlagSubmissionResponse
from app.services.auth_service import AuthService
from app.services.challenge_service import ChallengeService
from app.services.security import MAX_BCRYPT_PASSWORD_BYTES, create_access_token, to_utc_millis
from app.services.user_service import UserService


class CtfAcademyService:
    def __init__(
        self,
        auth_service: AuthService,
        challenge_service: ChallengeService,
        user_repo: UserRepositoryProtocol,
        challenge_repo: ChallengeRepositoryProtocol,
        leaderboard_repo: LeaderboardRepositoryProtocol,
    ) -> None:
        self._auth_service = auth_service
        self._challenge_service = challenge_service
        self._user_repo = user_repo
        self._challenge_repo = challenge_repo
        self._leaderboard_repo = leaderboard_repo

    async def build_state(self, user: Optional[User]) -> dict:
        entries = await self._leaderboard_repo.get_global_entries(limit=50)
        leaderboard = [
            {
                "username": entry.username,
                "score": entry.score,
                "durationMs": 0,
                "completedAt": to_utc_millis(entry.start_date),
            }
            for entry in entries
        ]

        participants = await self._leaderboard_repo.count_active_players()
        current_user_data = None
        session_data = None

        if user:
            solves = await self._user_repo.get_ordered_solves(user.id)
            completed_ids = [cid for cid, _ in solves]
            completion_times = {cid: to_utc_millis(solved_at) for cid, solved_at in solves}

            total_challenges = await self._challenge_repo.count_active()
            completed_at_ts = None
            if total_challenges > 0 and len(completed_ids) >= total_challenges and solves:
                completed_at_ts = to_utc_millis(solves[-1][1])

            global_rank = await self._leaderboard_repo.get_user_global_rank(user)
            rank_name = UserService.get_rank_name(user.score)
            created_ms = to_utc_millis(user.created_at)

            current_user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "nationality": user.nationality,
                "score": user.score,
                "rankName": rank_name,
                "rank_name": rank_name,
                "globalRank": global_rank,
                "global_rank": global_rank,
                "createdAt": created_ms,
                "created_at": created_ms,
                "startedAt": created_ms,
                "completedChallengeIds": completed_ids,
                "completionTimes": completion_times,
                "solvesCount": len(completed_ids),
                "solves_count": len(completed_ids),
                **({"completedAt": completed_at_ts} if completed_at_ts else {}),
            }
            session_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "nationality": user.nationality,
                "score": user.score,
                "isLoggedIn": True,
                "is_logged_in": True,
                "user": current_user_data,
            }

        return {
            "session": session_data,
            "currentUser": current_user_data,
            "leaderboard": leaderboard,
            "participants": participants,
        }

    async def register_academy_user(self, username: str, password: str) -> tuple[User, str]:
        clean_username = username.strip()
        if len(clean_username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario debe tener al menos 3 caracteres.",
            )
        if len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contrasena debe tener al menos 6 caracteres.",
            )
        if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La contrasena no puede superar los {MAX_BCRYPT_PASSWORD_BYTES} bytes.",
            )

        try:
            req = RegisterRequest(
                username=clean_username,
                email=f"{clean_username.lower()}@ctf.eclipsec.cl",
                password=password,
                nationality="CL",
            )
            user = await self._auth_service.register_user(req)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de usuario o contrasena invalido.",
            ) from exc
        except HTTPException as exc:
            detail = str(exc.detail).lower()
            if any(marker in detail for marker in ("already", "exist", "registered")):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ese usuario ya existe.",
                ) from exc
            raise HTTPException(
                status_code=exc.status_code,
                detail="No se pudo registrar el usuario.",
            ) from exc

        token = create_access_token(subject=user.id, token_type="web")
        return user, token

    async def login_academy_user(self, username: str, password: str) -> tuple[User, str]:
        clean_username = username.strip()
        if not clean_username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario y contrasena son requeridos.",
            )

        try:
            login_req = LoginRequest(username_or_email=clean_username, password=password)
            token_resp = await self._auth_service.authenticate_user(login_req, token_type="web")
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contrasena incorrectos.",
            ) from exc
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tu cuenta esta suspendida.",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contrasena incorrectos.",
            ) from exc

        user = await self._user_repo.get_by_id(token_resp.user.id, active_only=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contrasena incorrectos.",
            )
        return user, token_resp.access_token

    async def complete_challenge(
        self,
        user: User,
        challenge_id: str,
        submitted_flag: str,
    ) -> FlagSubmissionResponse:
        return await self._challenge_service.submit_flag(
            challenge_id_or_slug=challenge_id,
            submitted_flag=submitted_flag,
            user=user,
        )
