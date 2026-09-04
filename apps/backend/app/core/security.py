"""Security utilities: encryption, escaping, input sanitization."""
import base64
import hashlib
import html
import os
import re
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


# --- Sensitive data encryption (e.g., email tokens) ---
# Uses FERNET_KEY env or derives from SUPABASE_JWT_SECRET. Fallback is not for prod.
def _get_fernet() -> Fernet:
    key = os.environ.get("FERNET_KEY") or os.environ.get("SUPABASE_JWT_SECRET", "")
    if not key:
        # dev-only fallback: deterministic key (NOT secure for prod)
        key = "fixly-dev-fallback-not-for-production-1234"
    # Derive 32-byte urlsafe key via sha256
    digest = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)

_fernet = _get_fernet()

def encrypt_value(value: str) -> str:
    if not value:
        return value
    return _fernet.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    if not token:
        return token
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        # already plain or corrupted
        return token

# --- Input sanitization & escaping ---

# Allow letters, numbers, basic punctuation for titles; block script tags
_SCRIPT_RE = re.compile(r"<\s*script", re.I)
_HTML_TAG_RE = re.compile(r"<[^>]+>")

def sanitize_string(value: str, max_length: int = 5000, allow_html: bool = False) -> str:
    if not isinstance(value, str):
        return value
    value = value.strip()
    if len(value) > max_length:
        value = value[:max_length]
    if _SCRIPT_RE.search(value):
        raise ValueError("Potentially malicious content detected")
    if not allow_html:
        # Escape HTML to prevent XSS when rendered
        value = html.escape(value)
    return value

def sanitize_dict(data: dict[str, Any], max_str: int = 5000) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str):
            out[k] = sanitize_string(v, max_length=max_str)
        elif isinstance(v, dict):
            out[k] = sanitize_dict(v, max_str=max_str)
        elif isinstance(v, list):
            out[k] = [sanitize_string(x, max_str) if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    return out

# --- Block field tampering: allowed fields per resource ---

ALLOWED_ASSIGNMENT_FIELDS = {
    "title", "description", "subject_id", "priority", "status",
    "due_date", "estimated_study_time", "tags", "notes",
    "is_pinned", "is_favorite", "is_archived", "source", "ai_draft"
}
BLOCKED_FIELDS = {"user_id", "id", "created_at", "updated_at", "owner", "role", "is_admin"}

def strip_blocked_fields(payload: dict[str, Any], allowed: set[str] | None = None) -> dict[str, Any]:
    # Remove any blocked fields client should never set
    clean = {k: v for k, v in payload.items() if k not in BLOCKED_FIELDS}
    if allowed is not None:
        clean = {k: v for k, v in clean.items() if k in allowed}
    return clean

# --- Trim API responses: remove sensitive keys before returning ---

SENSITIVE_KEYS = {
    "access_token", "refresh_token", "token", "password", "secret",
    "service_role", "jwt_secret", "hashed_password",
}

def trim_response(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: trim_response(v) for k, v in data.items() if k.lower() not in SENSITIVE_KEYS}
    if isinstance(data, list):
        return [trim_response(x) for x in data]
    return data

def strip_email_tokens(account: dict[str, Any]) -> dict[str, Any]:
    """Return account without raw tokens; expose only has_token booleans."""
    out = {k: v for k, v in account.items() if k not in {"access_token", "refresh_token"}}
    out["has_access_token"] = bool(account.get("access_token"))
    out["has_refresh_token"] = bool(account.get("refresh_token"))
    return out
