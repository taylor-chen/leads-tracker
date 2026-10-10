from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None
    reply_to: str | None = None


class EmailSender(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Deliver a message. Raises on failure."""
