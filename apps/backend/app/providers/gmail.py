import base64
import re as re_mod
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.core.logging import get_logger
from app.providers.base import EmailProvider, SyncMessage, SyncResult

logger = get_logger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailProvider(EmailProvider):
    async def _refresh_token(self, account: dict[str, Any]) -> dict[str, Any]:
        refresh_token = account.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("No refresh token available for Gmail account")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

    async def _get_access_token(self, account: dict[str, Any]) -> str:
        expires_at = account.get("token_expires_at")
        if expires_at:
            try:
                exp_ts = datetime.fromisoformat(expires_at).timestamp()
                if time.time() < exp_ts - 60:
                    return str(account.get("access_token", ""))
            except (ValueError, TypeError):
                pass

        token_data: dict[str, Any] = await self._refresh_token(account)
        return str(token_data.get("access_token", account.get("access_token", "")))

    async def _gmail_get(
        self, access_token: str, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{GMAIL_API_BASE}/{path}"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

    async def validate(self, account: dict[str, Any]) -> bool:
        try:
            token = await self._get_access_token(account)
            await self._gmail_get(token, "profile")
            return True
        except Exception as e:
            logger.warning("Gmail validate failed: %s", e)
            return False

    async def fetch_messages(
        self,
        account: dict[str, Any],
        page_token: str | None = None,
        max_results: int = 50,
    ) -> SyncResult:
        token = await self._get_access_token(account)
        params: dict[str, Any] = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token

        list_data = await self._gmail_get(token, "messages", params)
        msg_ids = [m["id"] for m in list_data.get("messages", [])]

        messages = []
        for mid in msg_ids:
            try:
                full = await self._gmail_get(token, f"messages/{mid}", {"format": "full"})
                parsed = self._parse_gmail_message(full)
                messages.append(parsed)
            except Exception as e:
                logger.warning("Failed to fetch Gmail message %s: %s", mid, e)

        next_token = list_data.get("nextPageToken")
        history_id = list_data.get("resultSizeEstimate")
        return SyncResult(
            messages=messages,
            next_page_token=next_token,
            history_id=str(history_id) if history_id else None,
        )

    async def fetch_delta(
        self,
        account: dict[str, Any],
        history_id: str,
    ) -> SyncResult:
        token = await self._get_access_token(account)
        try:
            hist = await self._gmail_get(token, "history", {"startHistoryId": history_id})
        except Exception:
            logger.warning("History sync failed, falling back to full sync")
            return await self.fetch_messages(account)

        msg_ids = []
        for record in hist.get("history", []):
            for added in record.get("messagesAdded", []):
                msg = added.get("message", {})
                if msg.get("id"):
                    msg_ids.append(msg["id"])

        messages = []
        for mid in msg_ids:
            try:
                full = await self._gmail_get(token, f"messages/{mid}", {"format": "full"})
                parsed = self._parse_gmail_message(full)
                messages.append(parsed)
            except Exception as e:
                logger.warning("Failed to fetch delta message %s: %s", mid, e)

        new_history_id = str(hist.get("historyId", history_id))
        return SyncResult(messages=messages, history_id=new_history_id)

    async def mark_read(
        self,
        account: dict[str, Any],
        message_id: str,
    ) -> None:
        token = await self._get_access_token(account)
        url = f"{GMAIL_API_BASE}/messages/{message_id}/modify"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {"removeLabelIds": ["UNREAD"]}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()

    async def get_thread(
        self,
        account: dict[str, Any],
        thread_id: str,
    ) -> list[SyncMessage]:
        token = await self._get_access_token(account)
        thread_data = await self._gmail_get(token, f"threads/{thread_id}")
        messages = []
        for m in thread_data.get("messages", []):
            parsed = self._parse_gmail_message(m)
            messages.append(parsed)
        return messages

    def _parse_gmail_message(self, raw_msg: dict[str, Any]) -> SyncMessage:
        payload = raw_msg.get("payload", {})
        headers_dict: dict[str, str] = {}
        for h in payload.get("headers", []):
            headers_dict[h["name"].lower()] = h["value"]

        subject = headers_dict.get("subject", "")
        from_name, from_email = self._parse_from_header(headers_dict.get("from", ""))
        to_raw = headers_dict.get("to", "")
        to_emails = [e.strip() for e in to_raw.split(",") if e.strip()] if to_raw else []

        body_text = self._extract_body(payload)

        internal_date = raw_msg.get("internalDate", "")
        received_at = (
            datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).isoformat()
            if internal_date
            else datetime.now(timezone.utc).isoformat()
        )

        labels = raw_msg.get("labelIds", [])
        is_read = "UNREAD" not in labels
        is_starred = "STARRED" in labels
        has_attachments = self._has_attachments(payload)

        return SyncMessage(
            message_id=raw_msg["id"],
            thread_id=raw_msg.get("threadId"),
            subject=subject,
            from_name=from_name,
            from_email=from_email,
            to_emails=to_emails,
            body_text=body_text,
            received_at=received_at,
            is_read=is_read,
            is_starred=is_starred,
            has_attachments=has_attachments,
            labels=labels,
            raw=raw_msg,
        )

    def _parse_from_header(self, header: str) -> tuple[str | None, str]:
        match = re_mod.match(r'^(?:"?([^"]*)"?\s)?<?([^>]+)>?$', header.strip())
        if match:
            name = match.group(1) or None
            email = match.group(2) or header.strip()
            return name, email
        return None, header.strip()

    def _extract_body(self, payload: dict[str, Any]) -> str | None:
        mime = payload.get("mimeType", "")
        if mime == "text/plain" and payload.get("body", {}).get("data"):
            try:
                data = payload["body"]["data"]
                decoded = base64.urlsafe_b64decode(data)
                return decoded.decode("utf-8", errors="replace")
            except Exception:
                pass

        if mime == "text/html" and payload.get("body", {}).get("data"):
            try:
                data = payload["body"]["data"]
                decoded = base64.urlsafe_b64decode(data)
                text = decoded.decode("utf-8", errors="replace")
                text = re_mod.sub(r"<[^>]+>", " ", text)
                text = re_mod.sub(r"\s+", " ", text).strip()
                return text[:10000]
            except Exception:
                pass

        parts = payload.get("parts", [])
        for part in parts:
            result = self._extract_body(part)
            if result:
                return result

        return None

    def _has_attachments(self, payload: dict[str, Any]) -> bool:
        if payload.get("filename"):
            return True
        for part in payload.get("parts", []):
            if self._has_attachments(part):
                return True
        return False
