import asyncio
import email as email_lib
import imaplib
import time
from datetime import datetime, timezone
from email.header import decode_header
from typing import Any

from app.core.logging import get_logger
from app.providers.base import EmailProvider, SyncMessage, SyncResult

logger = get_logger(__name__)

IMAP_DEFAULTS: dict[str, dict[str, Any]] = {
    "outlook": {"host": "outlook.office365.com", "port": 993, "use_ssl": True},
    "yahoo": {"host": "imap.mail.yahoo.com", "port": 993, "use_ssl": True},
    "zoho": {"host": "imap.zoho.com", "port": 993, "use_ssl": True},
    "icloud": {"host": "imap.mail.me.com", "port": 993, "use_ssl": True},
    "other": {"host": "", "port": 993, "use_ssl": True},
}

MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY_S = 2


class IMAPProvider(EmailProvider):
    def __init__(self, provider_type: str = "other") -> None:
        self.provider_type = provider_type

    def _get_imap_config(self, account: dict[str, Any]) -> dict[str, Any]:
        defaults = IMAP_DEFAULTS.get(self.provider_type, IMAP_DEFAULTS["other"]).copy()
        return {
            "host": account.get("imap_host") or defaults["host"],
            "port": account.get("imap_port") or defaults["port"],
            "use_ssl": account.get("use_ssl", defaults["use_ssl"]),
        }

    def _connect(self, account: dict[str, Any]) -> imaplib.IMAP4:
        cfg = self._get_imap_config(account)
        email_addr = account.get("email", "")
        password = account.get("access_token", "")

        if cfg["use_ssl"]:
            conn: imaplib.IMAP4 = imaplib.IMAP4_SSL(cfg["host"], cfg["port"])
        else:
            conn = imaplib.IMAP4(cfg["host"], cfg["port"])
        conn.login(email_addr, password)
        return conn

    def _safe_connect(self, account: dict[str, Any]) -> imaplib.IMAP4:
        last_error = None
        for attempt in range(MAX_RECONNECT_ATTEMPTS):
            try:
                return self._connect(account)
            except Exception as e:
                last_error = e
                if attempt < MAX_RECONNECT_ATTEMPTS - 1:
                    time.sleep(RECONNECT_DELAY_S * (attempt + 1))
        raise last_error or RuntimeError("Failed to connect to IMAP server")

    async def validate(self, account: dict[str, Any]) -> bool:
        def _do_validate() -> bool:
            try:
                conn = self._connect(account)
                conn.logout()
                return True
            except Exception as e:
                logger.warning("IMAP validate failed: %s", e)
                return False

        return await asyncio.to_thread(_do_validate)

    async def fetch_messages(
        self,
        account: dict[str, Any],
        page_token: str | None = None,
        max_results: int = 50,
    ) -> SyncResult:
        known_uids = account.get("known_uids", [])
        last_uid = account.get("last_uid")

        def _fetch() -> SyncResult:
            conn = self._safe_connect(account)
            try:
                typ, data = conn.select("INBOX")
                if typ != "OK":
                    return SyncResult(messages=[])

                start_uid = last_uid or "1"
                typ, data = conn.uid("search", None, f"UID {start_uid}:*")  # type: ignore[arg-type]
                if typ != "OK" or not data[0]:
                    return SyncResult(messages=[])

                uid_bytes = data[0].split()
                all_uids = [u.decode() if isinstance(u, bytes) else u for u in uid_bytes]
                new_uids = [u for u in all_uids if u not in known_uids][-max_results:]

                messages = []
                for uid in new_uids:
                    try:
                        typ, msg_data = conn.uid("fetch", uid, "(RFC822 FLAGS)")
                        if typ != "OK" or not msg_data or not msg_data[0]:
                            continue
                        raw_email = msg_data[0][1]
                        flags = msg_data[0][0] if isinstance(msg_data[0], tuple) else b""
                        msg_obj = email_lib.message_from_bytes(raw_email)
                        sync_msg = self._parse_imap_message(uid, msg_obj, flags)
                        messages.append(sync_msg)
                    except Exception as e:
                        logger.warning("Failed to fetch IMAP msg UID %s: %s", uid, e)

                new_last_uid = all_uids[-1] if all_uids else last_uid
                return SyncResult(messages=messages, history_id=new_last_uid)
            finally:
                conn.logout()

        return await asyncio.to_thread(_fetch)

    async def fetch_delta(
        self,
        account: dict[str, Any],
        history_id: str,
    ) -> SyncResult:
        account["last_uid"] = history_id
        return await self.fetch_messages(account)

    async def mark_read(
        self,
        account: dict[str, Any],
        message_id: str,
    ) -> None:
        def _mark() -> None:
            try:
                conn = self._safe_connect(account)
                conn.select("INBOX")
                conn.uid("store", message_id, "+FLAGS", "(\\Seen)")
                conn.logout()
            except Exception as e:
                logger.warning("IMAP mark_read failed: %s", e)

        await asyncio.to_thread(_mark)

    async def get_thread(
        self,
        account: dict[str, Any],
        thread_id: str,
    ) -> list[SyncMessage]:
        return []

    def _parse_imap_message(
        self,
        uid: str,
        parsed: Any,
        flags: bytes,
    ) -> SyncMessage:
        subject = self._decode_header(parsed.get("Subject", ""))
        from_header = str(parsed.get("From", ""))
        from_name, from_email = self._parse_from_header(from_header)
        to_header = str(parsed.get("To", ""))
        to_emails = [e.strip() for e in to_header.split(",") if e.strip()]

        body_text = self._get_imap_body(parsed)
        date_str = str(parsed.get("Date", ""))
        received_at = self._parse_imap_date(date_str)
        is_read = b"\\Seen" in flags if flags else False
        has_attachment = self._has_attachments(parsed)

        return SyncMessage(
            message_id=uid,
            thread_id=parsed.get("Message-ID"),
            subject=subject,
            from_name=from_name,
            from_email=from_email,
            to_emails=to_emails,
            body_text=body_text,
            received_at=received_at,
            is_read=is_read,
            has_attachments=has_attachment,
            labels=[],
        )

    def _decode_header(self, value: Any) -> str:
        if not value:
            return ""
        parts = []
        for chunk, charset in decode_header(value):
            if isinstance(chunk, bytes):
                try:
                    parts.append(chunk.decode(charset or "utf-8", errors="replace"))
                except (LookupError, UnicodeDecodeError):
                    parts.append(chunk.decode("utf-8", errors="replace"))
            else:
                parts.append(str(chunk))
        return " ".join(parts)

    def _parse_from_header(self, header: str) -> tuple[str | None, str]:
        import re

        if not header:
            return None, ""
        match = re.match(r'^(?:"?([^"]*)"?\s)?<?([^>]+)>?$', header.strip())
        if match:
            return match.group(1) or None, match.group(2) or header.strip()
        return None, header.strip()

    def _get_imap_body(self, parsed: Any) -> str | None:
        body = None
        if parsed.is_multipart():
            for part in parsed.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset, errors="replace")[:10000]
                            break
                    except Exception:
                        pass
        else:
            try:
                payload = parsed.get_payload(decode=True)
                if payload:
                    charset = parsed.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")[:10000]
            except Exception:
                pass
        return body

    def _parse_imap_date(self, date_str: str) -> str:
        from email.utils import parsedate_to_datetime

        if not date_str:
            return datetime.now(timezone.utc).isoformat()
        try:
            dt = parsedate_to_datetime(date_str)
            if dt is None:
                return datetime.now(timezone.utc).isoformat()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()

    def _has_attachments(self, parsed: Any) -> bool:
        if not parsed.is_multipart():
            return False
        for part in parsed.walk():
            if part.get_content_maintype() == "multipart":
                continue
            filename = part.get_filename()
            if filename:
                return True
        return False
