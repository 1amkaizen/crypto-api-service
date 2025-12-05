# 📍 routers/crypto/send.py
import logging
from fastapi import APIRouter, HTTPException
from lib.native_sender import send_token

send_router = APIRouter()
logger = logging.getLogger(__name__)


@send_router.post(
    "/send/native",
    summary="Kirim Native Token",  # 🔹 teks yang muncul di Swagger UI
    description="Endpoint untuk mengirim native token seperti SOL, ETH, BNB, atau BASE ke wallet tujuan",
)
async def send_native_token(
    token: str,
    destination_wallet: str,
    amount: float,
    rpc_url: str = None,  # 🔹 user input RPC
    private_key: str = None,  # 🔹 user input private key untuk native token
):
    """Kirim native token ke wallet tujuan"""
    try:
        logger.info(
            f"🚀 Permintaan kirim {token.upper()} ke {destination_wallet} sejumlah {amount}"
        )

        # Kirim token (native token saja)
        tx_hash = await send_token(
            token,
            destination_wallet,
            amount,
            rpc_url=rpc_url,
            private_key=private_key,
        )

        if not tx_hash:
            # Kalo send_token gagal tapi ga raise exception
            raise HTTPException(
                status_code=400,
                detail=f"Transaksi gagal dijalankan. Periksa saldo atau wallet.",
            )

        return {
            "status": "success",
            "tx_hash": str(tx_hash),
            "message": f"{token.upper()} berhasil dikirim",
        }

    except ValueError as ve:
        logger.error(f"❌ Validation error: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"❌ Gagal kirim token: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
