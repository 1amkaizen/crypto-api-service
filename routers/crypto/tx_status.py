# 📍 routers/crypto/tx_status.py
import os
import logging
from fastapi import APIRouter, HTTPException
from solana.rpc.async_api import AsyncClient as SolanaClient
from web3 import AsyncWeb3, AsyncHTTPProvider

tx_status_router = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 🔹 Ambil RPC dari environment variables, fallback ke default public RPC
RPC_ENDPOINTS = {
    "eth": os.getenv(
        "ETH_RPC_URL", "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
    ),
    "bnb": os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/"),
    "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com/"),
    "sol": os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"),
    "trx": os.getenv("TRON_FULL_NODE", "https://api.trongrid.io"),
    "base": os.getenv("BASE_RPC_URL"),
}


@tx_status_router.get("/tx_status")
async def get_tx_status(chain: str, tx_hash: str):
    """
    🔹 Cek status transaksi berdasarkan tx_hash
    chain: "eth", "bnb", "polygon", "sol", "trx"
    """
    chain = chain.lower()
    try:
        if chain == "sol":
            logger.info(f"🔹 Mengecek status tx Solana: {tx_hash}")
            async with SolanaClient(RPC_ENDPOINTS["sol"]) as client:
                resp = await client.get_confirmed_transaction(tx_hash)
                if resp["result"] is None:
                    return {"status": "pending", "tx_hash": tx_hash}
                meta = resp["result"]["meta"]
                success = meta["err"] is None
                return {
                    "status": "success" if success else "failed",
                    "tx_hash": tx_hash,
                    "fee": meta.get("fee"),
                    "pre_balances": meta.get("preBalances"),
                    "post_balances": meta.get("postBalances"),
                }

        elif chain in ["eth", "bnb", "polygon"]:
            logger.info(f"🔹 Mengecek status tx {chain.upper()}: {tx_hash}")
            w3 = AsyncWeb3(AsyncHTTPProvider(RPC_ENDPOINTS[chain]))
            receipt = await w3.eth.get_transaction_receipt(tx_hash)
            if receipt is None:
                return {"status": "pending", "tx_hash": tx_hash}
            success = receipt.status == 1
            return {
                "status": "success" if success else "failed",
                "tx_hash": tx_hash,
                "blockNumber": receipt.blockNumber,
                "gasUsed": receipt.gasUsed,
                "logs": [dict(log) for log in receipt.logs],
            }

        elif chain == "trx":
            # 🔹 Placeholder TRX (TRON) support, nanti bisa pakai tronpy async
            logger.info(f"🔹 Mengecek status tx TRX (placeholder): {tx_hash}")
            return {
                "status": "pending",
                "tx_hash": tx_hash,
                "note": "TRX async belum diimplementasi",
            }

        else:
            raise HTTPException(status_code=400, detail=f"Chain {chain} tidak didukung")

    except Exception as e:
        logger.error(f"❌ Gagal cek tx_status [{chain}]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
