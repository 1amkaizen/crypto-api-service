# 📍 routers/crypto/tokens.py
import logging
from fastapi import APIRouter  # ✅ import yang diperlukan

tokens_router = APIRouter()  # 🔹 router khusus untuk tokens
logger = logging.getLogger(__name__)


@tokens_router.get("/tokens")
async def get_supported_tokens():
    tokens = ["BASE", "SOL", "ETH", "BNB", "TRX"]  # bisa dari config
    return {"status": "success", "tokens": tokens}
