# routers/users/api_key.py

import logging
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from lib.supabase_client import supabase

router = APIRouter()
logger = logging.getLogger("api_key")
logger.setLevel(logging.INFO)


# ---------- GENERATE API KEY ----------
@router.post("/generate-api-key")
async def generate_api_key(request: Request):
    # Ambil user_id dari cookie
    user_id = request.cookies.get("user_id")
    logger.info(f"[API_KEY] user_id cookie: {user_id}")

    if not user_id:
        logger.warning("[API_KEY] user_id tidak ditemukan")
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Generate kunci baru
    new_key = str(uuid.uuid4())
    logger.info(f"[API_KEY] Generated key: {new_key}")

    # Simpan ke Supabase
    insert_res = (
        supabase.table("APIKeys")
        .insert(
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "api_key": new_key,
                "is_active": True,
            }
        )
        .execute()
    )

    if insert_res.data:
        logger.info("[API_KEY] Key berhasil disimpan")
        return JSONResponse({"success": True, "api_key": new_key})

    logger.error(f"[API_KEY] Gagal insert: {insert_res}")
    return JSONResponse({"error": "Gagal generate API key"}, status_code=500)


# ============================================================
#                DELETE API KEY (BARU DITAMBAHKAN)
# ============================================================
@router.delete("/delete-api-key/{key_id}")
async def delete_api_key(request: Request, key_id: str):
    """Hapus API key berdasarkan id. Hanya untuk user yg login."""
    user_id = request.cookies.get("user_id")
    logger.info(f"[API_KEY-DELETE] user_id cookie: {user_id}, key_id: {key_id}")

    if not user_id:
        logger.warning("[API_KEY-DELETE] user_id tidak ditemukan")
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Pastikan API key itu milik user yang login
    key_res = (
        supabase.table("APIKeys")
        .select("*")
        .eq("id", key_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not key_res.data:
        logger.warning(
            f"[API_KEY-DELETE] Key bukan milik user atau tidak ditemukan: {key_id}"
        )
        return JSONResponse({"error": "API key tidak ditemukan"}, status_code=404)

    # Hapus key
    del_res = supabase.table("APIKeys").delete().eq("id", key_id).execute()

    if del_res.data:
        logger.info(f"[API_KEY-DELETE] Key berhasil dihapus: {key_id}")
        return JSONResponse({"success": True, "message": "API key berhasil dihapus"})

    logger.error(f"[API_KEY-DELETE] Gagal menghapus: {del_res}")
    return JSONResponse({"error": "Gagal menghapus API key"}, status_code=500)
