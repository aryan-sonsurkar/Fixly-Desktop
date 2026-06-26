import base64
import hashlib
import hmac
import json
import time
from typing import Any, cast

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

JWKS_CACHE: dict[str, Any] | None = None
JWKS_CACHE_EXPIRY: float = 0


def _get_jwks_url() -> str:
    return f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"


def _base64url_decode(input: str) -> bytes:
    rem = len(input) % 4
    if rem:
        input += "=" * (4 - rem)
    return base64.urlsafe_b64decode(input)


async def _fetch_jwks() -> dict[str, Any]:
    global JWKS_CACHE, JWKS_CACHE_EXPIRY
    now = time.time()
    if JWKS_CACHE and JWKS_CACHE_EXPIRY > now:
        return JWKS_CACHE
    async with httpx.AsyncClient() as client:
        response = await client.get(_get_jwks_url())
        response.raise_for_status()
        JWKS_CACHE = response.json()
        JWKS_CACHE_EXPIRY = now + 3600
        return JWKS_CACHE


def _get_kid_from_header(token: str) -> str | None:
    try:
        header_b64 = token.split(".")[0]
        header: dict[str, Any] = json.loads(_base64url_decode(header_b64))
        return cast(str, header.get("kid"))
    except (IndexError, json.JSONDecodeError, Exception):
        return None


def _verify_hmac_signature(token: str, secret: str) -> bool:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        signature = _base64url_decode(parts[2])
        message = f"{parts[0]}.{parts[1]}".encode("utf-8")
        expected = hmac.new(
            secret.encode("utf-8"), message, hashlib.sha256
        ).digest()
        return hmac.compare_digest(signature, expected)
    except Exception:
        return False


def _decode_payload(token: str) -> dict[str, Any] | None:
    try:
        payload_b64 = token.split(".")[1]
        result: dict[str, Any] = json.loads(_base64url_decode(payload_b64))
        return result
    except (IndexError, json.JSONDecodeError, Exception):
        return None


async def verify_token(token: str) -> dict[str, Any] | None:
    payload = _decode_payload(token)
    if not payload:
        return None

    exp = payload.get("exp", 0)
    if time.time() > exp:
        logger.debug("Token expired")
        return None

    aud = payload.get("aud")
    if aud and aud != "authenticated":
        logger.debug("Invalid token audience")
        return None

    is_valid = _verify_hmac_signature(token, settings.supabase_jwt_secret)
    if not is_valid:
        return None

    return payload


def get_user_id_from_token(token: str) -> str | None:
    payload = _decode_payload(token)
    if not payload:
        return None
    return payload.get("sub")


def get_user_email_from_token(token: str) -> str | None:
    payload = _decode_payload(token)
    if not payload:
        return None
    return payload.get("email")
