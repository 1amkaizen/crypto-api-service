# 📍 lib/monitor/usdt_dispatcher.py
import logging
from ecerbot.lib.monitor.usdt.eth_usdt import run_usdt_monitor as run_eth_usdt_monitor
from ecerbot.lib.monitor.usdt.bsc_usdt import run_usdt_monitor as run_bsc_usdt_monitor
from ecerbot.lib.monitor.usdt.sol_usdt import run_usdt_monitor as run_sol_usdt_monitor

# from ecerbot.lib.monitor.usdt.trx_usdt import run_usdt_monitor as run_trx_usdt_monitor
# from ecerbot.lib.monitor.usdt.base_usdt import run_usdt_monitor as run_base_usdt_monitor


logger = logging.getLogger(__name__)


async def run_usdt_monitor(order_id: str, chain: str):
    chain = chain.lower()

    if chain == "eth":
        return await run_eth_usdt_monitor(order_id, chain="eth")
    elif chain == "bsc":
        return await run_bsc_usdt_monitor(order_id, chain="bsc")
    elif chain == "sol":
        return await run_sol_usdt_monitor(order_id, chain="sol")
    # elif chain == "trx":
    #   return await run_trx_usdt_monitor(order_id, chain="trx")
    # elif chain == "base":
    #   return await run_base_usdt_monitor(order_id, chain="base")

    else:
        logger.error(f"❌ Chain {chain} belum didukung untuk USDT")
        raise ValueError(f"Chain {chain} belum didukung untuk USDT")
