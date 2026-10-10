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


def create_access_token(subject: str, settings: Settings) -> tuple[str, int]:
    """Return a signed JWT for `subject` and its lifetime in seconds."""
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(seconds=expires_in)}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Token has no subject")
    return subject
