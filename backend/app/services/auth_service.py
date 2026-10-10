import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthenticationError, InvalidCurrentPasswordError, ValidationError
from app.core.security import (
    InvalidTokenError,
    TokenClaims,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.base import utcnow
from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository

# Hash of a random throwaway value, checked when the email doesn't exist so that
# login takes about as long for unknown emails as for known ones (prevents user
# enumeration via timing). Nothing ever matches it, so it isn't a secret.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))

MIN_PASSWORD_LENGTH = 8
# bcrypt only uses the first 72 bytes of its input (and newer versions raise past that).
MAX_PASSWORD_BYTES = 72


def validate_password_policy(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        raise ValidationError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes")


class AuthService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)
        self.revoked = RevokedTokenRepository(db)

    def authenticate(self, email: str, password: str) -> tuple[str, int]:
        user = self.users.get_by_email(email)
        if user is None:
            verify_password(password, _DUMMY_HASH)
            raise AuthenticationError("Invalid email or password")
        if not verify_password(password, user.hashed_password) or not user.is_active:
            raise AuthenticationError("Invalid email or password")
        return create_access_token(str(user.id), user.token_version, self.settings)

    def user_from_token(self, token: str) -> User:
        claims = self._valid_claims(token)
        user = self.users.get(uuid.UUID(claims.subject))
        if user is None or not user.is_active or claims.version != user.token_version:
            raise AuthenticationError("Invalid or expired token")
        return user

    def change_password(self, user: User, *, current_password: str, new_password: str) -> None:
        """Replace `user`'s password and invalidate all of their existing tokens."""
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCurrentPasswordError("Current password is incorrect")
        validate_password_policy(new_password)
        if verify_password(new_password, user.hashed_password):
            raise ValidationError("New password must be different from the current password")
        user.hashed_password = hash_password(new_password)
        user.token_version += 1
        self.db.commit()

    def revoke_token(self, token: str) -> None:
        """Invalidate `token` before it expires (logout). Also prunes expired revocations."""
        claims = self._valid_claims(token)
        self.revoked.delete_expired(utcnow())
        self.revoked.add(claims.jti, claims.expires_at)
        self.db.commit()

    def _valid_claims(self, token: str) -> TokenClaims:
        try:
            claims = decode_access_token(token, self.settings)
            uuid.UUID(claims.subject)
        except (InvalidTokenError, ValueError) as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        if self.revoked.is_revoked(claims.jti):
            raise AuthenticationError("Invalid or expired token")
        return claims

    def create_user(self, *, email: str, password: str, full_name: str) -> User:
        validate_password_policy(password)
        if self.users.get_by_email(email) is not None:
            raise ValidationError("A user with this email already exists")
        user = self.users.add(
            User(
                email=email.strip().lower(),
                hashed_password=hash_password(password),
                full_name=full_name,
            )
        )
        self.db.commit()
        return user
