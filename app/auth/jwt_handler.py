from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config.settings import settings


def create_access_token(user_id: str, email: str) -> str:
    """
    Create a short-lived JWT access token (15 minutes by default).

    Payload includes:
        sub   — user ID (subject)
        email — user email
        type  — "access" to distinguish from refresh tokens
        exp   — expiry timestamp
        iat   — issued at timestamp
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.ACCESS_TOKEN_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, email: str) -> str:
    """
    Create a long-lived JWT refresh token (7 days by default).
    Used to issue new access tokens without re-login.

    Stored in DB token blacklist on logout to invalidate it.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.REFRESH_TOKEN_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate an access token.

    Returns:
        Decoded payload dict.

    Raises:
        ValueError: With a human-readable message for any invalid state.
    """
    try:
        payload = jwt.decode(
            token,
            settings.ACCESS_TOKEN_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            raise ValueError("Invalid token type.")
        return payload

    except ExpiredSignatureError:
        raise ValueError("Access token has expired. Please refresh your session.")
    except InvalidTokenError:
        raise ValueError("Invalid access token. Please log in again.")


def decode_refresh_token(token: str) -> dict:
    """
    Decode and validate a refresh token.

    Returns:
        Decoded payload dict.

    Raises:
        ValueError: With a human-readable message for any invalid state.
    """
    try:
        payload = jwt.decode(
            token,
            settings.REFRESH_TOKEN_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type.")
        return payload

    except ExpiredSignatureError:
        raise ValueError("Refresh token has expired. Please log in again.")
    except InvalidTokenError:
        raise ValueError("Invalid refresh token. Please log in again.")