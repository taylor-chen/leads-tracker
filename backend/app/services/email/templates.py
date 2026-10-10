from dataclasses import dataclass
from html import escape

from app.services.email.base import EmailMessage


@dataclass(frozen=True)
class LeadEmailContext:
    """Plain snapshot of a lead, safe to pass to a background task after the DB session closes."""

    lead_id: str
    first_name: str
    last_name: str
    email: str
    resume_filename: str


def prospect_confirmation(ctx: LeadEmailContext) -> EmailMessage:
    """Email thanking the prospect for their submission."""
    text = (
        f"Hi {ctx.first_name},\n\n"
        "Thanks for reaching out. We've received your information and resume. "
        "One of our attorneys will review it and get back to you shortly.\n\n"
        "Best regards,\nThe Legal Team"
    )
    html = (
        f"<p>Hi {escape(ctx.first_name)},</p>"
        "<p>Thanks for reaching out. We've received your information and resume. "
        "One of our attorneys will review it and get back to you shortly.</p>"
        "<p>Best regards,<br>The Legal Team</p>"
    )
    return EmailMessage(to=ctx.email, subject="We received your submission", text=text, html=html)


def attorney_notification(
    ctx: LeadEmailContext, *, to: str, frontend_base_url: str
) -> EmailMessage:
    """Email telling the attorney about a new lead, linking to it in the dashboard.

    Reply-To is the prospect, so the attorney can answer them directly.
    """
    full_name = f"{ctx.first_name} {ctx.last_name}"
    link = f"{frontend_base_url.rstrip('/')}/leads/{ctx.lead_id}"
    text = (
        "A new lead was submitted.\n\n"
        f"Name: {full_name}\n"
        f"Email: {ctx.email}\n"
        f"Resume: {ctx.resume_filename}\n\n"
        f"Review it here: {link}\n"
    )
    html = (
        "<p>A new lead was submitted.</p>"
        "<ul>"
        f"<li><strong>Name:</strong> {escape(full_name)}</li>"
        f"<li><strong>Email:</strong> {escape(ctx.email)}</li>"
        f"<li><strong>Resume:</strong> {escape(ctx.resume_filename)}</li>"
        "</ul>"
        f'<p><a href="{escape(link)}">Review the lead</a></p>'
    )
    return EmailMessage(
        to=to,
        subject=f"New lead: {full_name}",
        text=text,
        html=html,
        reply_to=ctx.email,
    )
