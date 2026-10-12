import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_supabase():
    """Create the production client lazily; tests override this dependency."""
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured")
    return create_client(url, key)
