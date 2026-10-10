import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import Settings


class InvalidTokenError(Exception):
    """The token is malformed, badly signed, expired or missing claims.

    Internal to the auth layer; `AuthService` turns it into an `AuthenticationError`.
    """


def hash_password(password: str) -> str:
    """Return a salted bcrypt hash of `password`."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Check `password` against a bcrypt hash. A malformed hash counts as a mismatch."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


@dataclass(frozen=True)
class TokenClaims:
    """The claims of a verified access token that the app relies on."""

    subject: str
    jti: str
    expires_at: datetime
    version: int


def create_access_token(subject: str, version: int, settings: Settings) -> tuple[str, int]:
    """Return a signed JWT for `subject` and its lifetime in seconds.

    `version` is the user's `token_version`; tokens carrying an older version are rejected.
    """
    expires_in = settings.access_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        # Unique token id, so a single token can be revoked on logout.
        "jti": secrets.token_urlsafe(16),
        "ver": version,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> TokenClaims:
    """Verify `token`'s signature and expiry and return its claims.

    Only checks the token itself; revocation and `token_version` are checked by
    `AuthService`. Raises `InvalidTokenError` if anything is wrong.
    """
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
    # Tokens issued before `ver` existed count as version 0, the column default.
    version = payload.get("ver", 0)
    if not subject or not jti:
        raise InvalidTokenError("Token is missing required claims")
    if not isinstance(version, int) or isinstance(version, bool):
        raise InvalidTokenError("Token has an invalid version claim")
    return TokenClaims(
        subject=subject,
        jti=jti,
        expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        version=version,
    )
