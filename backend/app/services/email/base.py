from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    """A provider-agnostic email. The sender sets the From address."""

    to: str
    subject: str
    text: str
    html: str | None = None
    reply_to: str | None = None


class EmailSender(ABC):
    """Interface for email delivery, so the transport can be swapped by config."""

    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Deliver a message. Raises on failure."""
