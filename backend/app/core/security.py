import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import Settings


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    jti: str
    expires_at: datetime


def create_access_token(subject: str, settings: Settings) -> tuple[str, int]:
    """Return a signed JWT for `subject` and its lifetime in seconds."""
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        # Unique token id, so a single token can be revoked on logout.
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "jti", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    subject, jti = payload["sub"], payload["jti"]
    if not subject or not jti:
        raise InvalidTokenError("Token is missing required claims")
    return TokenClaims(
        subject=subject, jti=jti, expires_at=datetime.fromtimestamp(payload["exp"], UTC)
    )
