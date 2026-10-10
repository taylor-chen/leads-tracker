"""Create users and leads tables

Revision ID: 0001
Revises:
Create Date: 2026-10-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

lead_state = sa.Enum("PENDING", "REACHED_OUT", name="lead_state")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("resume_key", sa.String(500), nullable=False),
        sa.Column("resume_filename", sa.String(255), nullable=False),
        sa.Column("resume_content_type", sa.String(100), nullable=False),
        sa.Column("resume_size_bytes", sa.Integer(), nullable=False),
        sa.Column("state", lead_state, nullable=False),
        sa.Column("reached_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reached_out_by_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_leads_email", "leads", ["email"])
    op.create_index("ix_leads_state", "leads", ["state"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_leads_created_at", table_name="leads")
    op.drop_index("ix_leads_state", table_name="leads")
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_table("leads")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    lead_state.drop(op.get_bind(), checkfirst=True)
