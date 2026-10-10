import logging
import uuid
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import InvalidStateTransitionError, NotFoundError
from app.db.base import utcnow
from app.models.lead import LEAD_STATE_TRANSITIONS, Lead, LeadState
from app.models.user import User
from app.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate, LeadUpdate
from app.services.email.templates import LeadEmailContext
from app.services.resume_validation import validate_resume
from app.services.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class LeadService:
    def __init__(self, db: Session, storage: StorageBackend, settings: Settings) -> None:
        self.db = db
        self.storage = storage
        self.settings = settings
        self.leads = LeadRepository(db)

    def create_lead(self, data: LeadCreate, resume: BinaryIO, resume_filename: str | None) -> Lead:
        validated = validate_resume(
            resume, resume_filename, max_bytes=self.settings.max_resume_bytes
        )
        key = self.storage.save(resume, suffix=validated.suffix)
        lead = Lead(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            resume_key=key,
            resume_filename=validated.filename,
            resume_content_type=validated.content_type,
            resume_size_bytes=validated.size_bytes,
            state=LeadState.PENDING,
        )
        try:
            self.leads.add(lead)
            self.db.commit()
        except Exception:
            self.db.rollback()
            # Don't leave orphaned files behind when the DB write fails.
            self.storage.delete(key)
            raise
        logger.info("Lead created id=%s", lead.id)
        return lead

    def list_leads(
        self, *, state: LeadState | None, page: int, page_size: int
    ) -> tuple[list[Lead], int]:
        return self.leads.list(state=state, offset=(page - 1) * page_size, limit=page_size)

    def get_lead(self, lead_id: uuid.UUID) -> Lead:
        lead = self.leads.get(lead_id)
        if lead is None:
            raise NotFoundError("Lead not found")
        return lead

    def update_lead(self, lead_id: uuid.UUID, data: LeadUpdate, actor: User) -> Lead:
        lead = self.get_lead(lead_id)
        if data.state != lead.state:
            if data.state not in LEAD_STATE_TRANSITIONS[lead.state]:
                raise InvalidStateTransitionError(
                    f"Cannot transition lead from {lead.state} to {data.state}"
                )
            lead.state = data.state
            if data.state == LeadState.REACHED_OUT:
                lead.reached_out_at = utcnow()
                lead.reached_out_by_id = actor.id
            self.db.commit()
            self.db.refresh(lead)
            logger.info("Lead id=%s moved to %s by user=%s", lead.id, lead.state, actor.id)
        return lead

    def resume_path(self, lead: Lead) -> Path:
        path = self.storage.path_for(lead.resume_key)
        if not path.exists():
            raise NotFoundError("Resume file not found")
        return path

    @staticmethod
    def email_context(lead: Lead) -> LeadEmailContext:
        return LeadEmailContext(
            lead_id=str(lead.id),
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            resume_filename=lead.resume_filename,
        )
