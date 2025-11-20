# 📍 lib/monitor/usdc_dispatcher.py
import logging
from lib.monitor.usdc.eth_usdc import run_usdc_monitor as run_eth_usdc_monitor
from lib.monitor.usdc.bsc_usdc import run_usdc_monitor as run_bsc_usdc_monitor
from lib.monitor.usdc.trx_usdc import run_usdc_monitor as run_trx_usdc_monitor
from lib.monitor.usdc.base_usdc import run_usdc_monitor as run_base_usdc_monitor
from lib.monitor.usdc.sol_usdc import run_usdc_monitor as run_sol_usdc_monitor

logger = logging.getLogger(__name__)


async def run_usdc_monitor(order_id: str, chain: str):
    chain = chain.lower()

    if chain == "eth":
        return await run_eth_usdc_monitor(order_id, chain="eth")
    elif chain == "bsc":
        return await run_bsc_usdc_monitor(order_id, chain="bsc")
    elif chain == "trx":
        return await run_trx_usdc_monitor(order_id, chain="trx")
    elif chain == "base":
        return await run_base_usdc_monitor(order_id, chain="base")
    elif chain == "sol":
        return await run_sol_usdc_monitor(order_id, chain="sol")
    else:
        logger.error(f"❌ Chain {chain} belum didukung untuk USDC")
        raise ValueError(f"Chain {chain} belum didukung untuk USDC")
