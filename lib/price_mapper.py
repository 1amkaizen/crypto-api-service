# 📍 lib/price_mapper.py
import logging
import httpx

logger = logging.getLogger(__name__)

# Mapping chain/token ke CoinGecko ID
COINGECKO_IDS = {
    "sol": "solana",
    "bnb": "binancecoin",
    "trx": "tron",
    "usdt": "tether",
    "usdc": "usd-coin",
    "ton": "the-open-network",
    "base": "base-protocol",
    "eth": "ethereum"  # ✅ perbaikan, sebelumnya salah pakai tether
}


async def get_token_amount(chain: str, nominal_idr: int) -> float:
    token_id = COINGECKO_IDS.get(chain.lower())
    if not token_id:
        logger.error(f"❌ Chain/token {chain} tidak dikenali")
        return 0

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=idr"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            price_idr = data.get(token_id, {}).get("idr")
            if not price_idr:
                logger.error(f"❌ Gagal ambil harga {chain.upper()} dari API CoinGecko")
                return 0
            amount = nominal_idr / price_idr
            amount = round(amount, 6)
            logger.info(f"💰 Nominal {nominal_idr} IDR = {amount} {chain.upper()} (harga {price_idr} IDR/{chain.upper()})")
            return amount
    except Exception as e:
        logger.exception(f"❌ Error ambil harga {chain.upper()} realtime: {e}")
        return 0

# 🔹 Tambahan: get_locked_token_amount
async def get_locked_token_amount(chain: str, nominal_idr: int) -> float:
    """
    Hitung jumlah token yang akan dikunci/locked.
    Bisa dikurangi fee atau multiplier tertentu jika mau.
    Contoh: 1% fee locked token.
    """
    base_amount = await get_token_amount(chain, nominal_idr)
    locked_amount = base_amount * 0.99  # contoh fee 1% untuk locked
    locked_amount = round(locked_amount, 6)
    logger.info(f"🔒 Locked token {chain.upper()}: {locked_amount} dari nominal {base_amount}")
    return locked_amount
