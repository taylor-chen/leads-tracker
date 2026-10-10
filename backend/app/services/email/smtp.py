import smtplib
from email.message import EmailMessage as MimeMessage

from app.core.config import Settings
from app.services.email.base import EmailMessage, EmailSender


class SmtpEmailSender(EmailSender):
    """Works with any SMTP relay: Mailpit locally, SES/SendGrid/Postmark in production."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, message: EmailMessage) -> None:
        mime = MimeMessage()
        mime["From"] = self.settings.email_from
        mime["To"] = message.to
        mime["Subject"] = message.subject
        if message.reply_to:
            mime["Reply-To"] = message.reply_to
        mime.set_content(message.text)
        if message.html:
            mime.add_alternative(message.html, subtype="html")

        s = self.settings
        smtp_cls = smtplib.SMTP_SSL if s.smtp_use_ssl else smtplib.SMTP
        with smtp_cls(s.smtp_host, s.smtp_port, timeout=10) as client:
            if s.smtp_starttls and not s.smtp_use_ssl:
                client.starttls()
            if s.smtp_username and s.smtp_password:
                client.login(s.smtp_username, s.smtp_password)
            client.send_message(mime)
