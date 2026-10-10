import logging

from app.services.email.base import EmailMessage, EmailSender

logger = logging.getLogger(__name__)


class ConsoleEmailSender(EmailSender):
    """Logs messages instead of sending them. Keeps an in-memory outbox for tests."""

    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.outbox.append(message)
        logger.info("Email to=%s subject=%r\n%s", message.to, message.subject, message.text)
