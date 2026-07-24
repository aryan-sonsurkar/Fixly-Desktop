import json
import re
import time
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.providers import get_provider
from app.repositories.ai_repository import AIRepository
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.email_repository import EmailRepository
from app.services.ai_service import AIService
from app.services.study_service import StudyService

logger = get_logger(__name__)

CATEGORIES = ["assignment", "exam", "project", "notice", "holiday", "event", "general", "spam"]
HIGH_CONFIDENCE = 0.95
MEDIUM_CONFIDENCE = 0.70


class EmailClassifier:
    """AI Email Classification via PromptManager."""

    def __init__(self) -> None:
        self.ai_service = AIService()
        self.ai_repo = AIRepository()

    async def classify(self, email: dict[str, Any], user_id: str) -> dict[str, Any]:
        subject = email.get("subject", "")
        body = (email.get("body_text") or "")[:3000]
        from_name = email.get("from_name", "")
        from_email = email.get("from_email", "")

        prompt = (
            f"Classify this academic email into exactly one category: "
            f"{', '.join(CATEGORIES)}.\n\n"
            f"From: {from_name} <{from_email}>\n"
            f"Subject: {subject}\n"
            f"Body:\n{body}\n\n"
            f"Respond with ONLY a JSON object containing:\n"
            f"- category: string (one of the categories above)\n"
            f"- confidence: float (0-1)\n"
            f"- reason: string (brief explanation)\n\n"
            f"If this email is about an assignment, also extract:\n"
            f"- assignment_subject: string or null\n"
            f"- assignment_title: string or null\n"
            f"- due_date: string (YYYY-MM-DD) or null\n"
            f"- priority: low|medium|high|urgent\n"
            f"- teacher_name: string or null\n"
            f"- course: string or null\n"
            f"- description: string or null"
        )

        conv = await self.ai_repo.create_conversation(user_id, "Email Classification")
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)
        content = result["message"]["content"]

        return self._parse_response(content)

    @staticmethod
    def _parse_response(content: str) -> dict[str, Any]:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                parsed: dict[str, Any] = json.loads(json_match.group(0))
                return parsed
            except json.JSONDecodeError:
                pass

        return {
            "category": "general",
            "confidence": 0.5,
            "reason": "Could not parse AI response",
            "assignment_subject": None,
            "assignment_title": None,
            "due_date": None,
            "priority": "medium",
            "teacher_name": None,
            "course": None,
            "description": None,
        }


class DuplicateDetector:
    """Prevent duplicate assignments from email."""

    def __init__(self) -> None:
        self.repository = EmailRepository()

    async def is_duplicate(self, email: dict[str, Any], user_id: str) -> bool:
        existing = await self.repository.get_messages_light(
            user_id, limit=100
        )
        for existing_email in existing:
            # Same email ID
            if existing_email.get("message_id") == email.get("message_id"):
                return True

            # Similar subject + same sender
            if (
                existing_email.get("from_email") == email.get("from_email")
                and existing_email.get("subject", "").strip().lower()
                == email.get("subject", "").strip().lower()
            ):
                return True

        return False


class EmailSyncWorker:
    def __init__(self) -> None:
        self.repository = EmailRepository()

    async def sync_account(self, account_id: str, user_id: str) -> dict[str, Any]:
        start = time.time()
        account = await self.repository.get_account(account_id, user_id)
        if not account:
            raise NotFoundError("Account not found")

        await self.repository.update_account(account_id, user_id, {"sync_status": "syncing"})

        synced = 0
        try:
            provider = get_provider(account.get("provider", "other"))
            history_id = account.get("history_id")

            if history_id:
                result = await provider.fetch_delta(account, history_id)
            else:
                result = await provider.fetch_messages(account)

            for sync_msg in result.messages:
                row = self._to_message_row(account, sync_msg)
                await self.repository.upsert_message(user_id, row)
                synced += 1

            updates: dict[str, Any] = {
                "sync_status": "idle",
                "total_emails": account.get("total_emails", 0) + synced,
                "last_synced_at": datetime.now(timezone.utc).isoformat(),
            }
            if result.history_id:
                updates["history_id"] = result.history_id
            await self.repository.update_account(account_id, user_id, updates)

            duration = int((time.time() - start) * 1000)
            return {"account_id": account_id, "synced": synced, "duration_ms": duration}

        except Exception as e:
            logger.error("Sync failed for account %s: %s", account_id, e)
            await self.repository.update_account(account_id, user_id, {
                "sync_status": "error",
                "sync_error": str(e),
            })
            raise

    @staticmethod
    def _to_message_row(account: dict[str, Any], msg: Any) -> dict[str, Any]:
        return {
            "user_id": account["user_id"],
            "account_id": account["id"],
            "message_id": msg.message_id,
            "thread_id": msg.thread_id,
            "subject": msg.subject,
            "from_name": msg.from_name,
            "from_email": msg.from_email,
            "to_emails": msg.to_emails,
            "body_text": msg.body_text,
            "received_at": msg.received_at,
            "is_read": msg.is_read,
            "is_starred": msg.is_starred,
            "has_attachments": msg.has_attachments,
            "labels": msg.labels,
        }


class EmailService:
    def __init__(self) -> None:
        self.repository = EmailRepository()
        self.classifier = EmailClassifier()
        self.detector = DuplicateDetector()
        self.sync_worker = EmailSyncWorker()
        self.ai_repo = AIRepository()
        self.ai_service = AIService()
        self.study_service = StudyService()
        self.assignment_repo = AssignmentRepository()

    # ── Accounts ──────────────────────────────────────────

    async def connect_account(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        existing = await self.repository.get_accounts(user_id)
        for acct in existing:
            if acct.get("email") == data.get("email"):
                raise ValueError("Account already connected")

        account = await self.repository.create_account(user_id, data)

        try:
            provider = get_provider(data.get("provider", "other"))
            valid = await provider.validate(account)
            await self.repository.update_account(account["id"], user_id, {
                "sync_status": "idle" if valid else "error",
                "sync_error": None if valid else "Provider validation failed",
            })
        except Exception as e:
            logger.warning("Provider validation failed for %s: %s", data.get("email"), e)
            await self.repository.update_account(account["id"], user_id, {
                "sync_status": "error",
                "sync_error": str(e),
            })

        return account

    async def get_accounts(self, user_id: str) -> list[dict[str, Any]]:
        return await self.repository.get_accounts(user_id)

    async def update_account(self, account_id: str, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await self.repository.update_account(account_id, user_id, data)

    async def delete_account(self, account_id: str, user_id: str) -> None:
        await self.repository.delete_account(account_id, user_id)

    async def sync_account(self, account_id: str, user_id: str) -> dict[str, Any]:
        result = await self.sync_worker.sync_account(account_id, user_id)
        await self._process_new_messages(account_id, user_id)
        return result

    async def _process_new_messages(self, account_id: str, user_id: str) -> None:
        messages, _ = await self.repository.get_messages(
            user_id, account_id=account_id, limit=50
        )
        for msg in messages:
            try:
                await self._classify_and_extract(msg, user_id)
            except Exception as e:
                logger.error("Failed to process message %s: %s", msg.get("id"), e)

    async def _classify_and_extract(self, msg: dict[str, Any], user_id: str) -> None:
        if msg.get("classification"):
            return

        cls = await self.classifier.classify(msg, user_id)
        category = cls.get("category", "general")
        confidence = cls.get("confidence", 0)

        await self.repository.create_classification(user_id, {
            "email_id": msg["id"],
            "user_id": user_id,
            "category": category,
            "confidence": confidence,
        })

        if category == "assignment" and confidence >= MEDIUM_CONFIDENCE:
            if await self.detector.is_duplicate(msg, user_id):
                logger.info("Skipping duplicate assignment: %s", msg.get("subject"))
                return

            asgn_data = {
                "email_id": msg["id"],
                "user_id": user_id,
                "subject": cls.get("assignment_subject"),
                "title": cls.get("assignment_title"),
                "due_date": cls.get("due_date"),
                "priority": cls.get("priority", "medium"),
                "teacher_name": cls.get("teacher_name"),
                "description": cls.get("description"),
                "course": cls.get("course"),
                "confidence": confidence,
            }

            if confidence >= HIGH_CONFIDENCE:
                asgn_data["status"] = "approved"
                try:
                    created = await self.assignment_repo.create_assignment(
                        user_id, {
                            "title": asgn_data.get("title") or msg.get("subject", "Untitled Assignment"),
                            "description": asgn_data.get("description"),
                            "subject_id": asgn_data.get("subject"),
                            "due_date": asgn_data.get("due_date"),
                            "priority": asgn_data.get("priority", "medium"),
                            "source": "email",
                        }
                    )
                    asgn_data["assignment_id"] = created.get("id")
                    asgn_data["status"] = "converted"
                except Exception as e:
                    logger.error("Failed to auto-create assignment: %s", e)
                    asgn_data["status"] = "pending"
            else:
                asgn_data["status"] = "pending"

            await self.repository.create_assignment(user_id, asgn_data)

    # ── Messages ──────────────────────────────────────────

    async def get_messages(
        self, user_id: str, account_id: str | None = None,
        limit: int = 50, offset: int = 0,
        unread_only: bool = False,
        search: str | None = None,
    ) -> dict[str, Any]:
        messages, total = await self.repository.get_messages(
            user_id, account_id, limit, offset, unread_only, search
        )
        return {"messages": messages, "total": total, "page": offset // limit + 1, "page_size": limit}

    async def get_message(self, message_id: str, user_id: str) -> dict[str, Any]:
        msg = await self.repository.get_message(message_id, user_id)
        if not msg:
            raise NotFoundError("Message not found")
        return msg

    async def mark_read(self, message_id: str, user_id: str) -> dict[str, Any]:
        return await self.repository.update_message(message_id, user_id, {"is_read": True})

    # ── Review Queue ──────────────────────────────────────

    async def get_review_queue(self, user_id: str) -> list[dict[str, Any]]:
        return await self.repository.get_review_queue(user_id)

    async def review_assignment(
        self, assignment_id: str, user_id: str, action: str,
        edits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = await self.repository.get_assignment(assignment_id, user_id)
        if not existing:
            raise NotFoundError("Assignment not found in review queue")

        updates: dict[str, Any] = {"status": action}

        if action == "approved" or action == "edited":
            try:
                create_data = {
                    "title": (edits or {}).get("title") or existing.get("title") or "Untitled",
                    "description": (edits or {}).get("description") or existing.get("description"),
                    "subject_id": (edits or {}).get("subject") or existing.get("subject"),
                    "due_date": (edits or {}).get("due_date") or existing.get("due_date"),
                    "priority": (edits or {}).get("priority") or existing.get("priority", "medium"),
                    "source": "email",
                }
                created = await self.assignment_repo.create_assignment(user_id, create_data)
                updates["assignment_id"] = created.get("id")
                updates["status"] = "converted"
            except Exception as e:
                logger.error("Failed to create assignment from review: %s", e)
                raise

        return await self.repository.update_assignment(assignment_id, user_id, updates)

    # ── Daily Briefing ────────────────────────────────────

    async def generate_briefing(self, user_id: str) -> dict[str, Any]:
        accounts = await self.repository.get_accounts(user_id)
        if not accounts:
            raise ValidationError("No email accounts connected")

        unread = await self.repository.get_unread_count(user_id)
        messages, _ = await self.repository.get_messages(user_id, limit=10)
        queue = await self.repository.get_review_queue(user_id)

        recent_emails_text = "\n".join(
            f"- {m.get('subject', 'No subject')} from {m.get('from_name', m.get('from_email', 'unknown'))}"
            for m in messages[:5]
        ) if messages else "No recent emails."

        queue_text = "\n".join(
            f"- {a.get('title', 'Untitled')} (confidence: {a.get('confidence', 0):.0%})"
            for a in queue[:5]
        ) if queue else "No pending reviews."

        prompt = (
            f"Generate a daily academic briefing for the student.\n"
            f"Unread emails: {unread}\n\n"
            f"Recent emails:\n{recent_emails_text}\n\n"
            f"Assignments pending review:\n{queue_text}\n\n"
            f"Include:\n"
            f"1. Summary of new emails\n"
            f"2. Detected assignments and deadlines\n"
            f"3. Study recommendations\n"
            f"4. Suggested focus areas\n"
            f"Keep it concise, motivational, and actionable."
        )

        conv = await self.ai_repo.create_conversation(user_id, "Daily Briefing")
        result = await self.ai_service.chat(user_id, prompt, conv["id"], stream=False)

        try:
            await self.study_service.log_session(user_id, {
                "activity_type": "ai_study",
                "duration_minutes": 1,
                "metadata": {"type": "daily_briefing"},
            })
        except Exception as e:
            logger.error("Failed to log briefing session: %s", e)

        return {
            "content": result["message"]["content"],
            "conversation_id": conv["id"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_unread_count(self, user_id: str) -> int:
        return await self.repository.get_unread_count(user_id)

    # ── Dashboard Stats ───────────────────────────────────

    async def get_dashboard_stats(self, user_id: str) -> dict[str, Any]:
        accounts = await self.repository.get_accounts(user_id)
        unread = await self.repository.get_unread_count(user_id)
        queue = await self.repository.get_review_queue(user_id)
        recent = await self.repository.get_recent_academic_emails(user_id, 5)

        return {
            "accounts_connected": len(accounts),
            "unread_academic": unread,
            "pending_review": len(queue),
            "recent_emails": recent,
            "last_sync": accounts[0].get("last_synced_at") if accounts else None,
        }
