# 📍 lib/coingecko.py
import aiohttp
import logging
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 🔹 URL Coingecko langsung, tidak dari env
BASE_URL = "https://api.coingecko.com/api/v3/simple/price"

TOKEN_MAP = {
    "sol": "solana",
    "eth": "ethereum",
    "usdt": "tether",
    "usdc": "usd-coin",
    "bnb": "binancecoin",
    "trx": "tron",
    "ton": "the-open-network",
    "base": "base-protocol",
}


async def get_current_price(token: str, retries=3, delay=1) -> float:
    coin_id = TOKEN_MAP.get(token.lower())
    if not coin_id:
        logger.warning(f"⚠️ Token {token} belum support")
        return 0

    params = {"ids": ",".join(TOKEN_MAP.values()), "vs_currencies": "idr,usd"}

    for attempt in range(1, retries + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(BASE_URL, params=params) as resp:
                    if resp.status != 200:
                        logger.error(
                            f"❌ Gagal fetch harga {token}, status: {resp.status}"
                        )
                        raise Exception("Status != 200")
                    data = await resp.json()
                    price_info = data.get(coin_id)
                    if not price_info:
                        logger.error(
                            f"❌ Token {token.upper()} tidak ada di respons API"
                        )
                        raise Exception("Token tidak ada")
                    price_idr = price_info.get("idr", 0)
                    price_usd = price_info.get("usd", 0)
                    if price_idr == 0 or price_usd == 0:
                        raise Exception("Data harga kosong")
                    kurs = price_idr / price_usd
                    logger.info(
                        f"💲 Harga real-time {token.upper()} : {price_idr:,.0f} IDR | {price_usd:.2f} USD | Kurs IDR/USD: {kurs:,.2f}"
                    )
                    return price_idr
        except Exception as e:
            logger.warning(
                f"⚠️ Attempt {attempt} gagal untuk {token}, retry in {delay}s"
            )
            await asyncio.sleep(delay)
    # fallback kalau semua retry gagal
    logger.error(f"❌ Semua attempt gagal, gunakan fallback price untuk {token}")
    return 0  # atau bisa pakai harga terakhir cache


async def log_all_prices():
    """Fetch & log semua harga token secara real-time"""
    for token in TOKEN_MAP.keys():
        await get_current_price(token)


async def get_current_sol_price() -> float:
    """Ambil harga SOL dalam IDR saja"""
    params = {"ids": "solana", "vs_currencies": "idr"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"❌ Gagal fetch harga SOL, status: {resp.status}")
                    return 0
                data = await resp.json()
                price = data.get("solana", {}).get("idr", 0)
                if price == 0:
                    logger.error(f"❌ Respons API tidak sesuai untuk SOL, data: {data}")
                return price
    except Exception as e:
        logger.exception("❌ Error ambil harga SOL")
        return 0
