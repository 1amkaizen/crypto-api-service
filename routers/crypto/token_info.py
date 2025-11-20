# 📍 routers/crypto/token_info.py
import logging
import httpx
from fastapi import APIRouter, HTTPException

token_info_router = APIRouter()
logger = logging.getLogger(__name__)

# 🔹 Mapping alias token populer ke CoinGecko ID
TOKEN_ALIAS = {
    "eth": "ethereum",
    "weth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "busd": "binance-usd",
    "usdt": "tether",
    "usdc": "usd-coin",
    "trx": "tron",
    "ton": "the-open-network",
    "ada": "cardano",
    "dot": "polkadot",
    "matic": "matic-network",
    "avax": "avalanche-2",
    "doge": "dogecoin",
    "shib": "shiba-inu",
    "ltc": "litecoin",
    "btc": "bitcoin",
    "atom": "cosmos",
    "dai": "dai",
    "ftm": "fantom",
    "cake": "pancakeswap-token",
    "matic": "matic-network",
    # 🔹 bisa tambah lagi sesuai kebutuhan
}


async def fetch_token_metadata_coingecko(token_id: str) -> dict:
    """
    Ambil metadata token dari CoinGecko API
    """
    url = f"https://api.coingecko.com/api/v3/coins/{token_id.lower()}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=404, detail=f"Token {token_id} tidak ditemukan di CoinGecko"
            )
        data = resp.json()
        metadata = {
            "name": data.get("name"),
            "symbol": data.get("symbol").upper() if data.get("symbol") else None,
            "decimals": (
                data.get("detail_platforms", {})
                .get("ethereum", {})
                .get("decimal_place")
                if "detail_platforms" in data
                else None
            ),
            "contract_address": (
                data.get("detail_platforms", {})
                .get("ethereum", {})
                .get("contract_address")
                if "detail_platforms" in data
                else None
            ),
            "coingecko_id": data.get("id"),
        }
        return metadata


@token_info_router.get("/token_info")
async def get_token_info(token: str):
    """
    Ambil metadata token dari CoinGecko secara real-time.
    User bisa pakai alias populer: sol -> solana, eth -> ethereum, dll.
    """
    try:
        # 🔹 Gunakan alias jika ada
        token_id = TOKEN_ALIAS.get(token.lower(), token.lower())
        metadata = await fetch_token_metadata_coingecko(token_id)
        logger.info(f"Token info diambil dari CoinGecko: {token} -> {token_id}")
        return {"status": "success", "token": token.lower(), "metadata": metadata}
    except HTTPException as he:
        logger.warning(f"Token {token} tidak ditemukan: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"❌ Gagal ambil token info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
