# 📍 lib/middleware/api_limit.py
import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from lib.supabase_client import supabase
from datetime import datetime, timezone, timedelta


logger = logging.getLogger("api_limit")
logger.setLevel(logging.INFO)

# Limit per API key
RATE_LIMIT = 60  # jumlah request
RATE_WINDOW = 60  # dalam detik


# Cache sementara di RAM (biar cepat)
# Struktur: { api_key: [timestamp1, timestamp2, ...] }
request_cache = {}


def get_rate_usage(api_key: str):
    """Hitung request terpakai & sisa untuk API key tertentu"""
    used = len(request_cache.get(api_key, []))
    remaining = max(0, RATE_LIMIT - used)
    return {
        "used": used,
        "remaining": remaining,
        "max": RATE_LIMIT,
        "window_seconds": RATE_WINDOW,
    }


async def api_rate_limit_middleware(request: Request, call_next):
    path = request.url.path

    # Hanya limit endpoint API, bukan dashboard, login, register
    if path.startswith("/api/"):

        api_key = request.headers.get("x-api-key")
        if not api_key:
            return JSONResponse({"error": "API key diperlukan"}, status_code=401)

        now = time.time()

        # Inisialisasi cache key
        if api_key not in request_cache:
            request_cache[api_key] = []

        # Bersihkan data lebih tua dari window
        request_cache[api_key] = [
            ts for ts in request_cache[api_key] if now - ts < RATE_WINDOW
        ]

        # Cek limit
        if len(request_cache[api_key]) >= RATE_LIMIT:
            logger.warning(f"[API_LIMIT] API key {api_key} melebihi limit")
            return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

        # Masukkan timestamp baru
        request_cache[api_key].append(now)

        # ========== CATAT KE DATABASE APIUsage ==========
        try:
            supabase.table("APIUsage").insert(
                {
                    "user_id": await get_user_id_from_key(api_key),
                    "endpoint": path,
                    "last_used": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.error(f"[API_LIMIT] Gagal insert usage: {e}")

    # Lanjut request
    return await call_next(request)


async def get_user_id_from_key(api_key: str):
    """Ambil user_id berdasarkan API key"""
    try:
        res = (
            supabase.table("APIKeys").select("user_id").eq("api_key", api_key).execute()
        )
        if res.data:
            return res.data[0]["user_id"]
    except Exception as e:
        logger.error(f"[API_LIMIT] Gagal lookup user_id: {e}")

    return None
