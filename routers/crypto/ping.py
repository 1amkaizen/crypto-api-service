# 📍 routers/crypto/ping.py
import logging
from fastapi import APIRouter

ping_router = APIRouter()
logger = logging.getLogger(__name__)


@ping_router.get("/ping")
async def ping():
    """Cek status API"""
    return {"status": "ok", "message": "Crypto API aktif"}
