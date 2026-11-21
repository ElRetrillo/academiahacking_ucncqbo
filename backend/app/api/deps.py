import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.repositories import (
    ChallengeRepositoryProtocol,
    LeaderboardRepositoryProtocol,
    SqlAlchemyChallengeRepository,
    SqlAlchemyLeaderboardRepository,
    SqlAlchemyTokenRevocationRepository,
    SqlAlchemyUserRepository,
    TokenRevocationRepositoryProtocol,
    UserRepositoryProtocol,
)
from app.services.auth_service import AuthService
from app.services.challenge_service import ChallengeService
from app.services.ctf_academy_service import CtfAcademyService
from app.services.leaderboard_service import LeaderboardService
from app.services.security import (
    FlagVerifier,
    HmacFlagVerifier,
    decode_token_payload,
    generate_csrf_token,
)
from app.services.user_service import UserService

http_bearer = HTTPBearer(auto_error=False)

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_LAST_CONNECTED_THROTTLE_SECONDS = 60


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepositoryProtocol:
    return SqlAlchemyUserRepository(db)


def get_challenge_repository(db: AsyncSession = Depends(get_db)) -> ChallengeRepositoryProtocol:
    return SqlAlchemyChallengeRepository(db)


def get_leaderboard_repository(db: AsyncSession = Depends(get_db)) -> LeaderboardRepositoryProtocol:
    return SqlAlchemyLeaderboardRepository(db)


def get_token_repository(db: AsyncSession = Depends(get_db)) -> TokenRevocationRepositoryProtocol:
    return SqlAlchemyTokenRevocationRepository(db)


def get_flag_verifier() -> FlagVerifier:
    return HmacFlagVerifier()


def get_auth_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo)


def get_challenge_service(
    challenge_repo: ChallengeRepositoryProtocol = Depends(get_challenge_repository),
    flag_verifier: FlagVerifier = Depends(get_flag_verifier),
) -> ChallengeService:
    return ChallengeService(challenge_repo=challenge_repo, flag_verifier=flag_verifier)


def get_leaderboard_service(
    leaderboard_repo: LeaderboardRepositoryProtocol = Depends(get_leaderboard_repository),
) -> LeaderboardService:
    return LeaderboardService(leaderboard_repo=leaderboard_repo)


def get_user_service(
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    leaderboard_repo: LeaderboardRepositoryProtocol = Depends(get_leaderboard_repository),
) -> UserService:
    return UserService(user_repo=user_repo, leaderboard_repo=leaderboard_repo)


def get_ctf_academy_service(
    auth_service: AuthService = Depends(get_auth_service),
    challenge_service: ChallengeService = Depends(get_challenge_service),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    challenge_repo: ChallengeRepositoryProtocol = Depends(get_challenge_repository),
    leaderboard_repo: LeaderboardRepositoryProtocol = Depends(get_leaderboard_repository),
) -> CtfAcademyService:
    return CtfAcademyService(
        auth_service=auth_service,
        challenge_service=challenge_service,
        user_repo=user_repo,
        challenge_repo=challenge_repo,
        leaderboard_repo=leaderboard_repo,
    )


def extract_token_from_request(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = None,
) -> tuple[Optional[str], bool]:
    """Return (token, is_cookie_auth) from Bearer header or HttpOnly session cookie."""
    if auth and auth.credentials:
        return auth.credentials, False

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token, False

    cookie_token = request.cookies.get(settings.COOKIE_NAME)
    if cookie_token:
        return cookie_token, True

    return None, False


def verify_csrf_if_cookie(request: Request, is_cookie_auth: bool) -> None:
    """Enforce double-submit CSRF verification for state-changing cookie requests."""
    if not is_cookie_auth or request.method not in _UNSAFE_METHODS:
        return

    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    csrf_header = request.headers.get("X-CSRF-Token")
    if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed.",
        )


def set_session_cookies(response: Response, token: str) -> None:
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    secure = settings.cookie_secure_effective
    samesite = settings.COOKIE_SAMESITE
    domain = settings.COOKIE_DOMAIN

    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=max_age,
        path="/",
        domain=domain,
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=generate_csrf_token(),
        httponly=False,
        secure=secure,
        samesite=samesite,
        max_age=max_age,
        path="/",
        domain=domain,
    )


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(key=settings.COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie(key=settings.CSRF_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)


async def is_token_revoked(
    token_repo: TokenRevocationRepositoryProtocol,
    jti: Optional[str],
) -> bool:
    if not jti:
        return False
    return await token_repo.is_revoked(jti)


async def revoke_token(
    token_repo: TokenRevocationRepositoryProtocol,
    token: str,
) -> None:
    payload = decode_token_payload(token)
    if not payload:
        return

    jti = payload.get("jti")
    if not jti:
        return

    exp_ts = payload.get("exp")
    if isinstance(exp_ts, (int, float)):
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc)

    await token_repo.revoke(str(jti), expires_at)


async def touch_last_connected(
    user_repo: UserRepositoryProtocol,
    user: User,
) -> None:
    now = datetime.now(timezone.utc)
    last = user.last_connected_at
    if last is not None:
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if (now - last).total_seconds() < _LAST_CONNECTED_THROTTLE_SECONDS:
            return

    await user_repo.touch_last_connected(user, now)


async def get_current_user_optional(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    token_repo: TokenRevocationRepositoryProtocol = Depends(get_token_repository),
) -> Optional[User]:
    token, _ = extract_token_from_request(request, auth)
    if not token:
        return None

    payload = decode_token_payload(token)
    if not payload or await is_token_revoked(token_repo, payload.get("jti")):
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await user_repo.get_by_id(str(user_id), active_only=True)
    if user:
        await touch_last_connected(user_repo, user)
    return user


async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    token_repo: TokenRevocationRepositoryProtocol = Depends(get_token_repository),
) -> User:
    token, is_cookie_auth = extract_token_from_request(request, auth)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token_payload(token)
    if not payload or await is_token_revoked(token_repo, payload.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    verify_csrf_if_cookie(request, is_cookie_auth)

    user_id = payload.get("sub")
    user = await user_repo.get_by_id(str(user_id), active_only=True) if user_id else None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await touch_last_connected(user_repo, user)
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return current_user
