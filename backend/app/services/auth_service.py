import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthenticationError, ValidationError
from app.core.security import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository

# Hash of a random throwaway value, checked when the email doesn't exist so that
# login takes about as long for unknown emails as for known ones (prevents user
# enumeration via timing). Nothing ever matches it, so it isn't a secret.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


class AuthService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> tuple[str, int]:
        user = self.users.get_by_email(email)
        if user is None:
            verify_password(password, _DUMMY_HASH)
            raise AuthenticationError("Invalid email or password")
        if not verify_password(password, user.hashed_password) or not user.is_active:
            raise AuthenticationError("Invalid email or password")
        return create_access_token(str(user.id), self.settings)

    def user_from_token(self, token: str) -> User:
        try:
            user_id = uuid.UUID(decode_access_token(token, self.settings))
        except (InvalidTokenError, ValueError) as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid or expired token")
        return user

    def create_user(self, *, email: str, password: str, full_name: str) -> User:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
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
