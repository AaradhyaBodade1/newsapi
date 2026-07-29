from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

import httpx

from common.credentials_store import get_credential
from common.enums import CredentialProvider
from common.settings_store import get_all_settings
from common.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def notify_job_failure(job_run_id: str, message: str) -> None:
    """Best-effort: sends via email (if SMTP + notification_email are
    configured) and/or a webhook (if configured). Every attempt — success or
    failure — is logged to notification_logs so failed notifications are
    themselves visible in the admin dashboard."""
    settings = get_all_settings()
    client = get_supabase()

    recipient = settings.get("notification_email")
    if recipient:
        _try_send(client, job_run_id, "email", lambda: _send_email(recipient, message))

    webhook_url = settings.get("notification_webhook_url")
    if webhook_url:
        _try_send(client, job_run_id, "webhook", lambda: _send_webhook(webhook_url, message))

    if not recipient and not webhook_url:
        logger.warning("Job run %s had failures but no notification channel is configured", job_run_id)


def _try_send(client, job_run_id: str, channel: str, send_fn) -> None:
    success = True
    error_message = ""
    try:
        send_fn()
    except Exception as exc:  # noqa: BLE001 - notification failures must not crash the worker
        success = False
        error_message = str(exc)[:500]
        logger.error("Failed to send %s notification: %s", channel, exc)

    client.table("notification_logs").insert(
        {
            "job_run_id": job_run_id,
            "channel": channel,
            "message": "sent" if success else error_message,
            "success": success,
        }
    ).execute()


def _send_email(recipient: str, message: str) -> None:
    host = get_credential(CredentialProvider.SMTP, "host")
    port = int(get_credential(CredentialProvider.SMTP, "port") or 587)
    username = get_credential(CredentialProvider.SMTP, "username")
    password = get_credential(CredentialProvider.SMTP, "password")
    if not host or not username or not password:
        raise RuntimeError("SMTP credentials are not fully configured")

    msg = MIMEText(message)
    msg["Subject"] = "News platform: worker job failure"
    msg["From"] = username
    msg["To"] = recipient

    with smtplib.SMTP(host, port, timeout=15) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(username, [recipient], msg.as_string())


def _send_webhook(url: str, message: str) -> None:
    resp = httpx.post(url, json={"text": message}, timeout=15)
    resp.raise_for_status()
