import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.lead import LeadState


class LeadCreate(BaseModel):
    """Text fields of the public lead form, trimmed and with the email lowercased."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_and_require(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class LeadUpdate(BaseModel):
    """Body of `PATCH /leads/{id}`. Only the state can change."""

    state: LeadState


class LeadSubmitted(BaseModel):
    """Public response for a submitted lead. Deliberately exposes no prospect data."""

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeInfo(BaseModel):
    """Metadata about a lead's uploaded resume."""

    filename: str
    content_type: str
    size_bytes: int


class UserSummary(BaseModel):
    """The attorney who acted on a lead, embedded in `LeadRead`."""

    id: uuid.UUID
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class LeadRead(BaseModel):
    """A lead as shown to signed-in attorneys."""

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    resume: ResumeInfo
    state: LeadState
    reached_out_at: datetime | None
    reached_out_by: UserSummary | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, lead) -> "LeadRead":
        """Build from a `Lead` row, nesting the flat `resume_*` columns under `resume`."""
        return cls(
            id=lead.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            resume=ResumeInfo(
                filename=lead.resume_filename,
                content_type=lead.resume_content_type,
                size_bytes=lead.resume_size_bytes,
            ),
            state=lead.state,
            reached_out_at=lead.reached_out_at,
            reached_out_by=(
                UserSummary.model_validate(lead.reached_out_by) if lead.reached_out_by else None
            ),
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )


class LeadPage(BaseModel):
    """One page of `GET /leads` results."""

    items: list[LeadRead]
    total: int
    page: int
    page_size: int
