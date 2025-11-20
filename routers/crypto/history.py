# 📍 routers/crypto/history.py
import logging
from fastapi import APIRouter, HTTPException  # ✅ import yang sebelumnya belum ada

history_router = APIRouter()  # 🔹 router khusus untuk history
logger = logging.getLogger(__name__)


@history_router.get("/history")
async def get_transaction_history(chain: str, wallet: str):
    """
    Ambil histori transaksi wallet tertentu di chain tertentu
    """
    # Contoh: dari helper log transaksi
    try:
        # dummy, nanti bisa pake DB atau explorer API
        history = []
        return {
            "status": "success",
            "chain": chain,
            "wallet": wallet,
            "history": history,
        }
    except Exception as e:
        logger.error(f"❌ Gagal ambil history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
