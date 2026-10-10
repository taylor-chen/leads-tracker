import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Database access for users. Flushes but never commits."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Look up a user by email, ignoring case and surrounding whitespace."""
        return self.db.scalar(select(User).where(User.email == email.strip().lower()))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user
