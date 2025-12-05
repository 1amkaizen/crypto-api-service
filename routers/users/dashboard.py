# 📍 routers/users/dashboard.py
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from lib.supabase_client import supabase
from lib.middleware import api_limit
from lib.middleware.api_limit import RATE_LIMIT, RATE_WINDOW
from collections import defaultdict

router = APIRouter()
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger("dashboard")
logger.setLevel(logging.INFO)


def parse_datetime(dt_str: str) -> datetime:
    """Parse timestamp dari Supabase ke datetime UTC"""
    try:
        if "." in dt_str:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.replace(tzinfo=timezone.utc)
    except:
        return None


async def get_rate_usage_from_db(user_id: str):
    """Hitung total request terpakai di window terakhir dari semua endpoint"""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=RATE_WINDOW)

    try:
        # Ambil semua APIUsage untuk user
        usage_res = (
            supabase.table("APIUsage")
            .select("count", "last_used")
            .eq("user_id", user_id)
            .execute()
        )
        usage_data = usage_res.data or []

        used = 0
        for u in usage_data:
            last_used = u.get("last_used")
            if not last_used:
                continue
            try:
                dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
            except Exception:
                continue
            # Masukin count kalau last_used masih di window
            if dt >= window_start:
                used += u.get("count", 0)

        remaining = max(0, RATE_LIMIT - used)
        logger.info(
            f"[DASHBOARD] User {user_id} rate_usage - used: {used}, remaining: {remaining}"
        )
        return {"used": used, "remaining": remaining}

    except Exception as e:
        logger.error(f"[DASHBOARD] Gagal hitung rate_usage dari DB: {e}")
        return {"used": 0, "remaining": RATE_LIMIT}


# ---------- DASHBOARD PAGE ----------
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user_id = request.cookies.get("user_id")
    logger.info(f"[DASHBOARD] user_id cookie: {user_id}")

    if not user_id:
        logger.warning("[DASHBOARD] user_id tidak ditemukan, redirect ke login")
        return RedirectResponse(url="/login", status_code=303)

    # Ambil data user
    res = supabase.table("Users").select("*").eq("id", user_id).execute()
    if not res.data:
        return RedirectResponse(url="/login", status_code=303)
    user = res.data[0]

    # Ambil API key user
    api_key_res = supabase.table("APIKeys").select("*").eq("user_id", user_id).execute()
    api_keys = api_key_res.data or []

    # Ambil semua API usage
    usage_res = supabase.table("APIUsage").select("*").eq("user_id", user_id).execute()
    raw_usage = usage_res.data or []

    # ================== API LIMIT ==================
    rate_limit_info = {
        "max_request": api_limit.RATE_LIMIT,
        "window_seconds": api_limit.RATE_WINDOW,
        "used": 0,
        "remaining": api_limit.RATE_LIMIT,
    }

    if api_keys:
        usage_info = await get_rate_usage_from_db(user_id)
        rate_limit_info["used"] = usage_info["used"]
        rate_limit_info["remaining"] = usage_info["remaining"]

    # --- Agregasi usage per endpoint ---
    usage_dict = defaultdict(lambda: {"count": 0, "last_used": None})
    for u in raw_usage:
        endpoint = u["endpoint"]
        usage_dict[endpoint]["count"] += u.get("count", 0)
        if (
            not usage_dict[endpoint]["last_used"]
            or u.get("last_used") > usage_dict[endpoint]["last_used"]
        ):
            usage_dict[endpoint]["last_used"] = u.get("last_used")

    usage_stats = [{"endpoint": k, **v} for k, v in usage_dict.items()]

    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "user": {
                "id": user["id"],
                "name": user.get("name"),
                "username": user.get("username"),
                "email": user.get("email"),
                "phone": user.get("phone"),
                "is_active": user.get("is_active"),
                "created_at": user.get("created_at"),
            },
            "api_keys": api_keys,
            "usage_stats": usage_stats,
            "rate_limit": rate_limit_info,
            "client_ip": request.client.host,
        },
    )
