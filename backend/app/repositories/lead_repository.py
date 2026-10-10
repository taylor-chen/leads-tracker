import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.lead import Lead, LeadState


class LeadRepository:
    """Database access for leads. Flushes but never commits; the service owns transactions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, lead: Lead) -> Lead:
        self.db.add(lead)
        self.db.flush()
        return lead

    def get(self, lead_id: uuid.UUID) -> Lead | None:
        return self.db.get(Lead, lead_id)

    def list_page(
        self, *, state: LeadState | None, offset: int, limit: int
    ) -> tuple[list[Lead], int]:
        """Return one page of leads, newest first, and the total matching `state`."""
        query = select(Lead)
        count_query = select(func.count()).select_from(Lead)
        if state is not None:
            query = query.where(Lead.state == state)
            count_query = count_query.where(Lead.state == state)

        total = self.db.scalar(count_query) or 0
        items = self.db.scalars(
            query.order_by(Lead.created_at.desc(), Lead.id).offset(offset).limit(limit)
        ).all()
        return list(items), total
