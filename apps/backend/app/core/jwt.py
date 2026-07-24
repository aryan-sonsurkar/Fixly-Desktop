import base64
import hashlib
import hmac
import json
import time
from typing import Any, cast

import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

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


def _get_header(token: str) -> dict[str, Any] | None:
    try:
        header_b64 = token.split(".")[0]
        return cast(dict[str, Any], json.loads(_base64url_decode(header_b64)))
    except (IndexError, json.JSONDecodeError, Exception):
        return None


def _get_kid_from_header(token: str) -> str | None:
    header = _get_header(token)
    if header:
        return cast(str, header.get("kid"))
    return None


def _get_alg_from_header(token: str) -> str | None:
    header = _get_header(token)
    if header:
        return cast(str, header.get("alg"))
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


def _verify_es256_signature(token: str, public_key: ec.EllipticCurvePublicKey) -> bool:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        raw_sig = _base64url_decode(parts[2])
        message = f"{parts[0]}.{parts[1]}".encode("utf-8")

        # Raw ECDSA signature is r||s (32 bytes each for P-256)
        if len(raw_sig) != 64:
            return False
        r = int.from_bytes(raw_sig[:32], "big")
        s = int.from_bytes(raw_sig[32:], "big")
        der_sig = utils.encode_dss_signature(r, s)

        public_key.verify(der_sig, message, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def _build_public_key_from_jwk(jwk: dict[str, Any]) -> ec.EllipticCurvePublicKey | None:
    try:
        x_bytes = _base64url_decode(jwk["x"])
        y_bytes = _base64url_decode(jwk["y"])
        x = int.from_bytes(x_bytes, "big")
        y = int.from_bytes(y_bytes, "big")
        return ec.EllipticCurvePublicNumbers(
            x, y, ec.SECP256R1()
        ).public_key()
    except Exception as e:
        logger.error("Failed to build EC public key from JWK", extra={"error": str(e)})
        return None


def _find_jwk_by_kid(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return cast(dict[str, Any], key)
    return None


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

    alg = _get_alg_from_header(token)

    if alg == "ES256":
        kid = _get_kid_from_header(token)
        if not kid:
            logger.debug("No kid in ES256 token header")
            return None
        try:
            jwks = await _fetch_jwks()
        except Exception as e:
            logger.error("Failed to fetch JWKS", extra={"error": str(e)})
            return None
        jwk = _find_jwk_by_kid(jwks, kid)
        if not jwk:
            logger.debug("No JWK found for kid %s", kid)
            return None
        public_key = _build_public_key_from_jwk(jwk)
        if not public_key:
            return None
        if not _verify_es256_signature(token, public_key):
            logger.debug("ES256 signature verification failed")
            return None
    elif alg == "HS256":
        if not settings.supabase_jwt_secret:
            logger.debug("HMAC secret not configured")
            return None
        if not _verify_hmac_signature(token, settings.supabase_jwt_secret):
            logger.debug("HMAC signature verification failed")
            return None
    else:
        logger.debug("Unsupported JWT algorithm: %s", alg)
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
