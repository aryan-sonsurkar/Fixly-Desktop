from supabase import Client, create_client

from app.config import settings

_supabase_client: Client | None = None
_supabase_service_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise RuntimeError("Supabase credentials not configured")
        _supabase_client = create_client(
            settings.supabase_url, settings.supabase_anon_key
        )
    return _supabase_client


def get_supabase_service() -> Client:
    global _supabase_service_client
    if _supabase_service_client is None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("Supabase service role key not configured")
        _supabase_service_client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
    return _supabase_service_client
