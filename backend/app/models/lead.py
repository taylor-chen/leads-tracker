import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.user import User


class LeadState(enum.StrEnum):
    """Where a lead is in the intake workflow."""

    PENDING = "PENDING"
    REACHED_OUT = "REACHED_OUT"


# Allowed state transitions. Kept as data so new states only need a new entry.
LEAD_STATE_TRANSITIONS: dict[LeadState, set[LeadState]] = {
    LeadState.PENDING: {LeadState.REACHED_OUT},
    LeadState.REACHED_OUT: set(),
}


class Lead(TimestampMixin, Base):
    """A prospect who submitted the public form, with their uploaded resume.

    The resume file itself lives in storage under `resume_key`; the other `resume_*`
    columns describe it. `reached_out_*` record who moved the lead to REACHED_OUT, and when.
    """

    __tablename__ = "leads"
    # Listing is ordered newest-first.
    __table_args__ = (Index("ix_leads_created_at", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)

    resume_key: Mapped[str] = mapped_column(String(500), nullable=False)
    resume_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resume_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    state: Mapped[LeadState] = mapped_column(
        Enum(LeadState, name="lead_state"),
        default=LeadState.PENDING,
        index=True,
        nullable=False,
    )
    reached_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reached_out_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    reached_out_by: Mapped[User | None] = relationship(lazy="joined")
