from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.config import Settings, get_settings
from app.models import ContactMessage, Workspace, WorkspaceMember

logger = logging.getLogger("chemvault.notifications")


@dataclass(slots=True)
class NotificationResult:
    sent: bool
    reason: str | None = None


def send_workspace_invite_notification(
    *,
    workspace: Workspace,
    member: WorkspaceMember,
    settings: Settings | None = None,
) -> NotificationResult:
    resolved = settings or get_settings()
    if not member.invited_email:
        return NotificationResult(sent=False, reason="invite has no email")
    invite_url = f"{resolved.app_url.rstrip('/')}/workspaces/invites/{member.invite_token}/accept"
    body = (
        f"You have been invited to join {workspace.name} on ChemVault Extract.\n\n"
        f"Role: {member.role}\n"
        f"Accept invite: {invite_url}\n\n"
        "If the link does not open, sign in with this email address and use the invite token below:\n"
        f"{member.invite_token}\n"
    )
    return _send_email(
        to_email=member.invited_email,
        subject=f"ChemVault Extract invite: {workspace.name}",
        body=body,
        settings=resolved,
    )


def send_contact_notification(
    *,
    message: ContactMessage,
    settings: Settings | None = None,
) -> NotificationResult:
    resolved = settings or get_settings()
    if not resolved.contact_notification_email:
        return NotificationResult(sent=False, reason="CONTACT_NOTIFICATION_EMAIL is not configured")
    body = (
        "New ChemVault Extract contact message\n\n"
        f"Name: {message.name}\n"
        f"Email: {message.email}\n"
        f"Role: {message.role or ''}\n"
        f"Organization: {message.organization or ''}\n\n"
        f"{message.message}\n"
    )
    return _send_email(
        to_email=resolved.contact_notification_email,
        subject="New ChemVault Extract contact message",
        body=body,
        reply_to=message.email,
        settings=resolved,
    )


def _send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    settings: Settings,
    reply_to: str | None = None,
) -> NotificationResult:
    if not settings.smtp_host or not settings.smtp_from_email:
        return NotificationResult(sent=False, reason="SMTP_HOST or SMTP_FROM_EMAIL is not configured")

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.notification_timeout_seconds) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Email notification failed: %s", exc)
        return NotificationResult(sent=False, reason=str(exc))
    return NotificationResult(sent=True)
