import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, Query, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, EmailSenderDep, LeadServiceDep, SettingsDep
from app.models.lead import LeadState
from app.schemas.lead import LeadPage, LeadRead, LeadSubmission, LeadSubmitted, LeadUpdate
from app.services.notifications import send_lead_submitted_emails

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadSubmitted, status_code=status.HTTP_201_CREATED)
def create_lead(
    background_tasks: BackgroundTasks,
    service: LeadServiceDep,
    email_sender: EmailSenderDep,
    settings: SettingsDep,
    form: Annotated[LeadSubmission, Form()],
) -> LeadSubmitted:
    """Public endpoint: submit a lead with a resume. Sends emails to the prospect and attorney."""
    lead = service.create_lead(form, form.resume.file, form.resume.filename)
    background_tasks.add_task(
        send_lead_submitted_emails, email_sender, settings, service.email_context(lead)
    )
    return LeadSubmitted.model_validate(lead)


@router.get("", response_model=LeadPage)
def list_leads(
    service: LeadServiceDep,
    _: CurrentUser,
    state: LeadState | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> LeadPage:
    """List leads newest first, optionally filtered by state."""
    items, total = service.list_leads(state=state, page=page, page_size=page_size)
    return LeadPage(
        items=[LeadRead.from_model(lead) for lead in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: uuid.UUID, service: LeadServiceDep, _: CurrentUser) -> LeadRead:
    return LeadRead.from_model(service.get_lead(lead_id))


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: uuid.UUID, body: LeadUpdate, service: LeadServiceDep, user: CurrentUser
) -> LeadRead:
    """Change a lead's state (PENDING → REACHED_OUT), recording who did it."""
    return LeadRead.from_model(service.update_lead(lead_id, body, actor=user))


@router.get("/{lead_id}/resume", response_class=FileResponse)
def download_resume(lead_id: uuid.UUID, service: LeadServiceDep, _: CurrentUser) -> FileResponse:
    lead = service.get_lead(lead_id)
    return FileResponse(
        service.resume_path(lead),
        media_type=lead.resume_content_type,
        filename=lead.resume_filename,
    )
