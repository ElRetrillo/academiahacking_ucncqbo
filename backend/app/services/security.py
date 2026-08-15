import hmac
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt, JWTError
from app.config import settings


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def hash_flag(flag: str) -> str:
    return hashlib.sha256(flag.strip().encode("utf-8")).hexdigest()


def verify_flag(submitted_flag: str, expected_flag: str, expected_hash: Optional[str] = None) -> bool:
    """Constant-time flag verification to prevent side-channel timing attacks."""
    submitted = submitted_flag.strip()
    
    # 1. Direct constant-time string comparison
    if hmac.compare_digest(submitted, expected_flag.strip()):
        return True
        
    # 2. Compare against SHA-256 hash if provided
    if expected_hash:
        submitted_hash = hash_flag(submitted)
        if hmac.compare_digest(submitted_hash, expected_hash):
            return True
            
    return False


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
