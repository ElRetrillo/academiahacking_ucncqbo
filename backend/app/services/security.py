import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Protocol, Union

import bcrypt
from jose import JWTError, jwt

from app.config import settings

REDACTED_FLAG_MARKER = "[REDACTED]"


class FlagVerifier(Protocol):
    def verify(
        self,
        submitted_flag: str,
        expected_flag: Optional[str],
        expected_hash: Optional[str] = None,
    ) -> bool:
        ...


class HmacFlagVerifier:
    """Constant-time flag verifier backed by HMAC-SHA256."""

    def hash(self, flag: str, secret: Optional[str] = None) -> str:
        key = (secret if secret is not None else settings.FLAG_HMAC_SECRET).encode("utf-8")
        return hmac.new(key, flag.strip().encode("utf-8"), hashlib.sha256).hexdigest()

    def verify(
        self,
        submitted_flag: str,
        expected_flag: Optional[str],
        expected_hash: Optional[str] = None,
    ) -> bool:
        submitted = submitted_flag.strip()
        if not submitted:
            return False

        if expected_hash:
            if hmac.compare_digest(self.hash(submitted), expected_hash):
                return True
            if expected_flag and expected_flag != REDACTED_FLAG_MARKER:
                legacy_sha256 = hashlib.sha256(submitted.encode("utf-8")).hexdigest()
                if hmac.compare_digest(legacy_sha256, expected_hash):
                    return True

        if expected_flag and expected_flag != REDACTED_FLAG_MARKER:
            if hmac.compare_digest(submitted, expected_flag.strip()):
                return True

        return False


_default_flag_verifier = HmacFlagVerifier()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def hash_flag(flag: str, secret: Optional[str] = None) -> str:
    return _default_flag_verifier.hash(flag, secret=secret)


def verify_flag(
    submitted_flag: str,
    expected_flag: Optional[str],
    expected_hash: Optional[str] = None,
) -> bool:
    return _default_flag_verifier.verify(submitted_flag, expected_flag, expected_hash)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "cli",
) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        minutes = (
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
            if token_type == "web"
            else settings.CLI_TOKEN_EXPIRE_MINUTES
        )
        expire = now + timedelta(minutes=minutes)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "jti": str(uuid.uuid4()),
        "typ": token_type,
        "iat": now,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token_payload(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[str]:
    payload = decode_token_payload(token)
    return payload.get("sub") if payload else None
