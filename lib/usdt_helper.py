# lib/usdt_helper.py
import logging
from lib.helpers.usdt.eth import send_usdt_eth
from lib.helpers.usdt.bsc import send_usdt_bsc
from lib.helpers.usdt.trx import send_usdt_trx
from lib.helpers.usdt.base import send_usdt_base
from lib.helpers.usdt.sol import send_usdt_solana

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# router
async def send_usdt(destination_wallet: str, amount: float, chain: str):
    chain = chain.lower()
    if chain == "eth":
        return await send_usdt_eth(destination_wallet, amount)
    elif chain == "bsc":
        return await send_usdt_bsc(destination_wallet, amount)
    elif chain == "trx":
        return await send_usdt_trx(destination_wallet, amount)
    elif chain == "base":
        return await send_usdt_base(destination_wallet, amount)
    elif chain == "sol":
        # pakai loop.run_in_executor biar synchronous jadi awaitable
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, send_usdt_solana, destination_wallet, amount)
    else:
        raise ValueError(f"Chain {chain} tidak didukung untuk USDT!")
