# 📍 routers/crypto/balance.py
import logging
from fastapi import APIRouter, HTTPException
from lib.balance_checker import check_balance  # ✅ import yang diperlukan

balance_router = APIRouter()  # 🔹 router khusus untuk balance
logger = logging.getLogger(__name__)


@balance_router.get("/balance")
async def get_wallet_balance(chain: str, wallet: str):
    """Cek saldo wallet per chain"""
    try:
        bal = await check_balance(chain, wallet)
        return {
            "status": "success",
            "chain": chain.upper(),
            "wallet": wallet,
            "balance": bal,
        }
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
