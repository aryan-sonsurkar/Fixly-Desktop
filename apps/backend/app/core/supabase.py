from httpx import Client as HttpxClient
from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from app.config import settings

_supabase_anon_client: Client | None = None
_supabase_service_client: Client | None = None


def _build_client(supabase_key: str, jwt_token: str | None = None) -> Client:
    headers = {}
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"

    return create_client(
        settings.supabase_url,
        supabase_key,
        options=SyncClientOptions(
            headers=headers,
            httpx_client=HttpxClient(
                http2=False,
                follow_redirects=True,
                timeout=30,
                headers=headers
            )
        ),
    )


def get_supabase() -> Client:
    global _supabase_anon_client
    if _supabase_anon_client is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise RuntimeError("Supabase credentials not configured")
        _supabase_anon_client = _build_client(settings.supabase_anon_key)
    return _supabase_anon_client


def get_supabase_for_user(access_token: str) -> Client:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("Supabase credentials not configured")
    return _build_client(settings.supabase_anon_key, access_token)


def get_supabase_service() -> Client:
    global _supabase_service_client
    if _supabase_service_client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("Supabase service role key not configured")
        _supabase_service_client = _build_client(settings.supabase_service_role_key)
    return _supabase_service_client
