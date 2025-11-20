# 📍 routers/crypto/estimate_gas.py
import logging
from fastapi import APIRouter, HTTPException
from lib.crypto_sender import estimate_gas_fee  # ✅ import yang diperlukan

estimate_gas_router = APIRouter()  # 🔹 router khusus untuk estimate gas
logger = logging.getLogger(__name__)


@estimate_gas_router.get("/estimate-gas")
async def estimate_gas(chain: str, token: str, destination_wallet: str, amount: float):
    """
    Estimasi biaya gas untuk transaksi token tertentu
    """
    try:
        gas_fee = await estimate_gas_fee(token, chain, destination_wallet, amount)
        return {"status": "success", "gas_fee": gas_fee}
    except Exception as e:
        logger.error(f"❌ Gagal estimate gas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
