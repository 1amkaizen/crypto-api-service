# 📍 routers/crypto/price.py
import logging
from fastapi import APIRouter, HTTPException
from lib.coingecko import get_current_price  # ✅ import yang diperlukan

price_router = APIRouter()  # 🔹 router khusus untuk price
logger = logging.getLogger(__name__)


@price_router.get("/price")
async def get_token_price(token: str):
    """Dapatkan harga real-time token dalam IDR"""
    try:
        price = await get_current_price(token)
        if price == 0:
            raise HTTPException(
                status_code=404, detail=f"Harga {token.upper()} tidak tersedia"
            )
        return {"status": "success", "token": token.upper(), "price_idr": price}
    except Exception as e:
        logger.error(f"❌ Gagal ambil harga token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
