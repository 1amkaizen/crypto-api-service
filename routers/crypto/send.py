# 📍 routers/crypto/send.py
import logging
from fastapi import APIRouter, HTTPException
from lib.crypto_sender import send_token

send_router = APIRouter()  # 🔹 router khusus untuk send
logger = logging.getLogger(__name__)


@send_router.post("/send")  # 🔹 pakai send_router, bukan router
async def send_crypto(
    token: str,
    chain: str,
    destination_wallet: str,
    amount: float,
    order_id: str = None,
    user_id: int = None,
    username: str = None,
    full_name: str = None,
):
    """Kirim token ke wallet tujuan"""
    try:
        logger.info(
            f"🚀 Permintaan kirim {token.upper()} ke {destination_wallet} sejumlah {amount}"
        )
        tx_hash = await send_token(
            token,
            chain,
            destination_wallet,
            amount,
            order_id,
            user_id,
            username,
            full_name,
        )
        if not tx_hash:
            raise HTTPException(status_code=400, detail="Transaksi gagal dijalankan")
        return {
            "status": "success",
            "tx_hash": str(tx_hash),
            "message": f"{token.upper()} berhasil dikirim",
        }
    except Exception as e:
        logger.error(f"❌ Gagal kirim token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
