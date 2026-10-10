from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.revoked_token import RevokedToken


class RevokedTokenRepository:
    """Database access for the token denylist. Flushes but never commits."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def is_revoked(self, jti: str) -> bool:
        return self.db.get(RevokedToken, jti) is not None

    def add(self, jti: str, expires_at: datetime) -> None:
        """Revoke the token `jti`. Revoking the same token twice is a no-op."""
        if not self.is_revoked(jti):
            self.db.add(RevokedToken(jti=jti, expires_at=expires_at))
            self.db.flush()

    def delete_expired(self, now: datetime) -> None:
        self.db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))
