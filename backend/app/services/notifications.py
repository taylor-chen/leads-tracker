import logging

from app.core.config import Settings
from app.services.email.base import EmailSender
from app.services.email.templates import (
    LeadEmailContext,
    attorney_notification,
    prospect_confirmation,
)

logger = logging.getLogger(__name__)


def send_lead_submitted_emails(
    sender: EmailSender, settings: Settings, ctx: LeadEmailContext
) -> None:
    """Notify the prospect and the attorney about a new lead.

    Runs as a background task after the lead is committed. Each email is sent
    independently so one failure doesn't block the other; failures are logged
    rather than surfaced to the prospect. In production this would move to a
    durable queue (e.g. SQS/Celery) with retries.
    """
    messages = [
        prospect_confirmation(ctx),
        attorney_notification(
            ctx,
            to=settings.attorney_notification_email,
            frontend_base_url=settings.frontend_base_url,
        ),
    ]
    for message in messages:
        try:
            sender.send(message)
        except Exception:
            logger.exception(
                "Failed to send email lead_id=%s subject=%r", ctx.lead_id, message.subject
            )
