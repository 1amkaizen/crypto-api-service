# 📍 routers/crypto/wallet_monitor.py
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from lib.monitor.solana import SolanaMonitor
from lib.monitor.eth import EthereumMonitor
from lib.monitor.bsc import BSCMonitor

logger = logging.getLogger(__name__)
monitor_router = APIRouter()

active_listeners = {}  # key: "{chain}_{wallet}", value: task

CHAIN_MAP = {
    "sol": "solana",
    "solana": "solana",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "bsc": "binance",
    "binance": "binance",
    "bnb": "binance",
}


@monitor_router.post("/subscribe")
async def subscribe_wallet(chain: str = "solana", wallet: str = None):
    """
    🔹 Subscribe wallet untuk listen transaksi
    chain: 'sol', 'eth', 'bsc', dll
    wallet: wallet yang mau didengar
    """
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet harus diisi")

    resolved_chain = CHAIN_MAP.get(chain.lower())
    if not resolved_chain:
        raise HTTPException(status_code=400, detail=f"Chain tidak valid: {chain}")

    key = f"{resolved_chain}_{wallet}"
    if key in active_listeners:
        raise HTTPException(status_code=400, detail="Listener sudah aktif")

    # assign wallet yang mau didengar ke monitor
    if resolved_chain == "solana":
        monitor = SolanaMonitor()
        monitor.wallet_admin = wallet
        task = asyncio.create_task(monitor.subscribe_account())
    elif resolved_chain == "ethereum":
        monitor = EthereumMonitor()
        monitor.wallet_admin = wallet
        task = asyncio.create_task(monitor.subscribe_pending_txs())
    elif resolved_chain == "binance":
        monitor = BSCMonitor()
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
