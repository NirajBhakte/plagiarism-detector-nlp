# src/supabase_client.py

import os
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client


def is_supabase_configured() -> bool:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip() or os.getenv(
        "SUPABASE_KEY", ""
    ).strip()
    return bool(url and key)


@lru_cache(maxsize=1)
def get_supabase() -> Optional[Client]:
    """
    Returns a Supabase client when SUPABASE_URL and a key are set.
    Prefer SUPABASE_SERVICE_ROLE_KEY on the backend (bypasses RLS for server writes).
    """
    if not is_supabase_configured():
        return None

    url = os.environ["SUPABASE_URL"].strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ["SUPABASE_KEY"].strip()
    )
    return create_client(url, key)
