from functools import lru_cache
from supabase import create_client, Client
from config import settings


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Anon client — for user-scoped operations using the caller's JWT."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    """Service-role client — bypasses RLS, used for pipeline writes and auth verification."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
