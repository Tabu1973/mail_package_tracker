"""IMAP client helper for Mail Package Tracker."""
from __future__ import annotations

from datetime import datetime, timedelta
import email
from email.header import decode_header
from email.message import Message
import imaplib
import logging
from typing import Any

from .parser import clean_email_body

_LOGGER = logging.getLogger(__name__)

_IMAP_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _decode_mime_header(raw_header: str | None) -> str:
    """Decode RFC2047 MIME-encoded email header."""
    if not raw_header:
        return ""
    parts: list[str] = []
    for chunk, charset in decode_header(raw_header):
        if isinstance(chunk, bytes):
            enc = charset or "utf-8"
            try:
                parts.append(chunk.decode(enc, errors="replace"))
            except LookupError:
                parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(str(chunk))
    return "".join(parts).strip()


def _extract_body_parts(msg: Message) -> tuple[str, str]:
    """Extract (plain_text, html_text) from an email.message.Message."""
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition") or "")
            if "attachment" in content_disp.lower():
                continue
            if content_type not in ("text/plain", "text/html"):
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if content_type == "text/plain":
                plain_parts.append(decoded)
            elif content_type == "text/html":
                html_parts.append(decoded)
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            if content_type == "text/html":
                html_parts.append(decoded)
            else:
                plain_parts.append(decoded)

    return "\n".join(plain_parts).strip(), "\n".join(html_parts).strip()


def format_imap_since_date(days_back: int) -> str:
    """Format a date N days ago as DD-Mon-YYYY for standard IMAP SINCE search."""
    target = datetime.now() - timedelta(days=max(1, days_back))
    month_str = _IMAP_MONTHS[target.month - 1]
    return f"{target.day:02d}-{month_str}-{target.year}"


def fetch_recent_emails_sync(
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str = "INBOX",
    days_back: int = 2,
    max_emails: int = 40,
) -> list[dict[str, Any]]:
    """Connect to IMAP server and fetch recent emails from the last `days_back` days."""
    if not host or not user or not password:
        return []

    messages: list[dict[str, Any]] = []
    conn: imaplib.IMAP4_SSL | None = None
    try:
        conn = imaplib.IMAP4_SSL(host, int(port), timeout=20)
        conn.login(user, password)
        status, _ = conn.select(f'"{folder}"' if " " in folder else folder, readonly=True)
        if status != "OK":
            _LOGGER.warning("Could not select IMAP folder %s", folder)
            return []

        since_str = format_imap_since_date(days_back)
        status, data = conn.uid("SEARCH", None, f"(SINCE {since_str} UNDELETED)")
        if status != "OK" or not data or not data[0]:
            return []

        uid_list = data[0].split()
        # Take the newest `max_emails` UIDs
        recent_uids = uid_list[-max_emails:]
        recent_uids.reverse()  # newest first

        for uid_bytes in recent_uids:
            uid_str = uid_bytes.decode("ascii", errors="ignore")
            # Fetch at most the first 300 KB (headers + text/html body) without downloading multi-MB attachments
            f_status, msg_data = conn.uid("FETCH", uid_bytes, "(BODY.PEEK[]<0.300000>)")
            if f_status != "OK" or not msg_data:
                continue

            raw_bytes = b""
            for item in msg_data:
                if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
                    raw_bytes = item[1]
                    break
            if not raw_bytes:
                continue

            msg = email.message_from_bytes(raw_bytes)
            sender = _decode_mime_header(msg.get("From"))
            subject = _decode_mime_header(msg.get("Subject"))
            date_hdr = _decode_mime_header(msg.get("Date"))
            msg_id = _decode_mime_header(msg.get("Message-ID")) or f"imap_{uid_str}"

            plain_text, html_text = _extract_body_parts(msg)
            clean_text, urls = clean_email_body(plain_text, html_text)

            messages.append(
                {
                    "imap_uid": uid_str,
                    "message_id": msg_id,
                    "sender": sender,
                    "subject": subject,
                    "date": date_hdr,
                    "text": clean_text,
                    "html": html_text,
                    "urls": urls,
                }
            )
    except Exception as err:
        _LOGGER.error("Error fetching emails via IMAP from %s: %s", host, err)
        raise
    finally:
        if conn is not None:
            try:
                conn.logout()
            except Exception:
                pass

    return messages


def test_imap_connection_sync(
    host: str,
    port: int,
    user: str,
    password: str,
    folder: str = "INBOX",
) -> bool:
    """Verify IMAP credentials and folder access."""
    conn: imaplib.IMAP4_SSL | None = None
    try:
        conn = imaplib.IMAP4_SSL(host, int(port), timeout=15)
        conn.login(user, password)
        status, _ = conn.select(f'"{folder}"' if " " in folder else folder, readonly=True)
        return status == "OK"
    finally:
        if conn is not None:
            try:
                conn.logout()
            except Exception:
                pass
