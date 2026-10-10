from app.core.config import Settings
from app.services.email.base import EmailMessage, EmailSender
from app.services.email.console import ConsoleEmailSender
from app.services.email.smtp import SmtpEmailSender


def build_email_sender(settings: Settings) -> EmailSender:
    """Return the sender selected by `EMAIL_BACKEND`."""
    if settings.email_backend == "smtp":
        return SmtpEmailSender(settings)
    return ConsoleEmailSender()


__all__ = [
    "ConsoleEmailSender",
    "EmailMessage",
    "EmailSender",
    "SmtpEmailSender",
    "build_email_sender",
]
