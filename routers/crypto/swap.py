# 📍 routers/crypto/swap.py
import logging
import httpx
from fastapi import APIRouter, HTTPException

swap_router = APIRouter()
logger = logging.getLogger(__name__)

# Mapping token ke CoinGecko ID
COINGECKO_IDS = {
    "sol": "solana",
    "eth": "ethereum",
    "bnb": "binancecoin",
    "usdt": "tether",
    "usdc": "usd-coin",
    "trx": "tron",
    "ton": "the-open-network",
}


async def get_token_price_usd(token: str) -> float:
    """Ambil harga token dalam USD dari CoinGecko"""
    token_id = COINGECKO_IDS.get(token.lower())
    if not token_id:
        raise HTTPException(status_code=400, detail=f"Token {token} tidak didukung")
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        data = resp.json()
        price = data.get(token_id, {}).get("usd")
        if price is None:
            raise HTTPException(status_code=500, detail=f"Gagal ambil harga {token}")
        return price


@swap_router.post("/swap")
async def swap_tokens(
    from_token: str, to_token: str, amount: float, user_id: int = None
):
    """
    Swap token dari satu jenis ke jenis lain berdasarkan harga real-time CoinGecko
    """
    try:
        price_from = await get_token_price_usd(from_token)
        price_to = await get_token_price_usd(to_token)

        # hitung swapped_amount = jumlah from_token dikali rate to_token
        swapped_amount = amount * price_from / price_to

        # terapkan fee 1%
        swapped_amount = swapped_amount * 0.99

        logger.info(
            f"User {user_id} swap {amount} {from_token} → {swapped_amount:.6f} {to_token}"
        )

        return {
            "status": "success",
            "from_token": from_token,
            "to_token": to_token,
            "swapped_amount": round(swapped_amount, 6),
            "price_from_usd": price_from,
            "price_to_usd": price_to,
        }

    except Exception as e:
        logger.error(f"❌ Swap gagal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
