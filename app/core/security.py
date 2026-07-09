from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings


# Password hashing
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _USE_FALLBACK = False
except Exception:  # pragma: no cover - backend issues possible in some envs
    logging.warning("bcrypt backend not available; falling back to sha256_crypt")
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    _USE_FALLBACK = True


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        # fallback to a more portable algorithm if bcrypt fails
        fallback = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
        return fallback.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        fallback = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
        return fallback.verify(plain_password, hashed_password)


# JWT helpers
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as exc:
        raise
