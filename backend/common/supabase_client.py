"""Server-side Supabase client factory, shared by the backend and worker.

Both services use the SERVICE ROLE key (bypasses Row Level Security) because
they act as the trusted server. This client must never be shipped to the
frontend — the frontend uses the anon key with RLS enforced instead.
"""
from __future__ import annotations

import os
from functools import lru_cache

from supabase import Client, create_client


class SupabaseConfigError(RuntimeError):
    pass


@lru_cache
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_role_key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the environment."
        )
    return create_client(url, service_role_key)
