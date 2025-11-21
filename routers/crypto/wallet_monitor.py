# 📍 routers/crypto/wallet_monitor.py
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from lib.monitor.solana import SolanaMonitor
from lib.monitor.eth import EthereumMonitor

logger = logging.getLogger(__name__)
monitor_router = APIRouter()

active_listeners = {}  # key: "{chain}_{wallet}", value: task

# 🔹 Mapping nama chain / alias
# 🔹 Mapping chain / alias
CHAIN_MAP = {
    # Solana
    "sol": "solana",
    "solana": "solana",
    # Ethereum
    "eth": "ethereum",
    "ethereum": "ethereum",
    # Binance Smart Chain
    "bsc": "binance",
    "binance": "binance",
    "bnb": "binance",
    # Tron
    "trx": "tron",
    "tron": "tron",
    # Polygon / Matic
    "matic": "polygon",
    "polygon": "polygon",
    # USDT / USDC (stablecoins bisa map ke chain default)
    "usdt": "ethereum",
    "usdc": "ethereum",
    # Avalanche
    "avax": "avalanche",
    "avalanche": "avalanche",
    # Ton
    "ton": "ton",
    # Tambahan lain bisa langsung ditambah disini
}


@monitor_router.post("/subscribe")
async def subscribe_wallet(chain: str = "solana", wallet: str = None):
    """
    🔹 Subscribe wallet untuk listen transaksi
    chain: bisa pakai alias seperti 'sol', 'solana', 'eth', 'ethereum'
    wallet: wallet admin yang mau didengar
    """
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet harus diisi")

    resolved_chain = CHAIN_MAP.get(chain.lower())
    if not resolved_chain:
        raise HTTPException(status_code=400, detail=f"Chain tidak valid: {chain}")

    key = f"{resolved_chain}_{wallet}"
    if key in active_listeners:
        raise HTTPException(status_code=400, detail="Listener sudah aktif")

    if resolved_chain == "solana":
        monitor = SolanaMonitor()
        monitor.wallet_admin = wallet
        task = asyncio.create_task(monitor.subscribe_account())
    elif resolved_chain == "ethereum":
        monitor = EthereumMonitor()
        monitor.wallet_admin = wallet
        task = asyncio.create_task(monitor.subscribe_pending_txs())
    else:
        raise HTTPException(status_code=400, detail="Chain belum didukung")

    active_listeners[key] = task
    logger.info(f"✅ Listener aktif | chain={resolved_chain} wallet={wallet}")
    return {
        "status": "success",
        "message": f"Listener {resolved_chain} untuk wallet {wallet} aktif",
    }


@monitor_router.post("/unsubscribe")
async def unsubscribe_wallet(chain: str = "solana", wallet: str = None):
    """
    🔹 Stop listener
    """
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet harus diisi")

    resolved_chain = CHAIN_MAP.get(chain.lower())
    if not resolved_chain:
        raise HTTPException(status_code=400, detail=f"Chain tidak valid: {chain}")

    key = f"{resolved_chain}_{wallet}"
    task = active_listeners.get(key)
    if task:
        task.cancel()
        del active_listeners[key]
        logger.info(f"✅ Listener dihentikan | chain={resolved_chain} wallet={wallet}")
        return {
            "status": "success",
            "message": f"Listener {resolved_chain} untuk wallet {wallet} dihentikan",
        }
    raise HTTPException(status_code=404, detail="Listener tidak ditemukan")
