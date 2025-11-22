# lib/middleware/api_usage.py

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from lib.supabase_client import supabase

logger = logging.getLogger("api_usage")
logger.setLevel(logging.INFO)


class APIUsageMiddleware(BaseHTTPMiddleware):
    """Middleware untuk mencatat penggunaan API berdasarkan API Key."""

    async def dispatch(self, request, call_next):
        try:
            # Ambil API Key dari Header
            api_key = request.headers.get("X-API-Key")

            # Kalau tidak ada API Key → biarkan lewat
            if not api_key:
                return await call_next(request)

            # Ambil user_id berdasarkan APIKeys
            key_res = (
                supabase.table("APIKeys").select("*").eq("api_key", api_key).execute()
            )

            if not key_res.data:
                logger.warning(f"[API-USAGE] API Key tidak valid: {api_key}")
                return await call_next(request)

            user_id = key_res.data[0]["user_id"]
            endpoint = request.url.path

            # --- Cek apakah user + endpoint sudah ada ---
            usage_res = (
                supabase.table("APIUsage")
                .select("*")
                .eq("user_id", user_id)
                .eq("endpoint", endpoint)
                .execute()
            )

            if usage_res.data:
                # --- UPDATE count + last_used ---
                usage_id = usage_res.data[0]["id"]
                current_count = usage_res.data[0]["count"]

                supabase.table("APIUsage").update(
                    {
                        "count": current_count + 1,
                        "last_used": "now()",
                    }
                ).eq("id", usage_id).execute()

                logger.info(
                    f"[API-USAGE] UPDATE user={user_id} endpoint={endpoint} count={current_count + 1}"
                )

            else:
                # --- INSERT record baru ---
                supabase.table("APIUsage").insert(
                    {
                        "user_id": user_id,
                        "endpoint": endpoint,
                        "count": 1,
                    }
                ).execute()

                logger.info(
                    f"[API-USAGE] INSERT user={user_id} endpoint={endpoint} count=1"
                )

        except Exception as e:
            logger.error(f"[API-USAGE] Error: {e}")

        return await call_next(request)
