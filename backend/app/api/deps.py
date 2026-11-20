import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.services.security import decode_token_payload, generate_csrf_token

http_bearer = HTTPBearer(auto_error=False)

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_LAST_CONNECTED_THROTTLE_SECONDS = 60


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


async def is_token_revoked(db: AsyncSession, jti: Optional[str]) -> bool:
    if not jti:
        return False
    res = await db.execute(select(RevokedToken.jti).where(RevokedToken.jti == jti))
    return res.scalar_one_or_none() is not None


async def revoke_token(db: AsyncSession, token: str) -> None:
    payload = decode_token_payload(token)
    if not payload:
        return

    jti = payload.get("jti")
    if not jti or await is_token_revoked(db, str(jti)):
        return

    exp_ts = payload.get("exp")
    if isinstance(exp_ts, (int, float)):
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    else:
        expires_at = datetime.now(timezone.utc)

    db.add(RevokedToken(jti=str(jti), expires_at=expires_at))
    await db.commit()


async def touch_last_connected(db: AsyncSession, user: User) -> None:
    now = datetime.now(timezone.utc)
    last = user.last_connected_at
    if last is not None:
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if (now - last).total_seconds() < _LAST_CONNECTED_THROTTLE_SECONDS:
            return

    user.last_connected_at = now
    await db.commit()


async def get_current_user_optional(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    token, _ = extract_token_from_request(request, auth)
    if not token:
        return None

    payload = decode_token_payload(token)
    if not payload or await is_token_revoked(db, payload.get("jti")):
        return None

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()

    if user:
        await touch_last_connected(db, user)

    return user


async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token, is_cookie_auth = extract_token_from_request(request, auth)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token_payload(token)
    if not payload or await is_token_revoked(db, payload.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    verify_csrf_if_cookie(request, is_cookie_auth)

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await touch_last_connected(db, user)
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
