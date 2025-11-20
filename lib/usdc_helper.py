# lib/usdc_helper.py
import logging
from lib.helpers.usdc.eth import send_usdc_eth
from lib.helpers.usdc.bsc import send_usdc_bsc
from lib.helpers.usdc.trx import send_usdc_trx
from lib.helpers.usdc.base import send_usdc_base
from lib.helpers.usdc.sol import send_usdc_solana

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# router
async def send_usdc(destination_wallet: str, amount: float, chain: str):
    chain = chain.lower()
    if chain == "eth":
        return await send_usdc_eth(destination_wallet, amount)
    elif chain == "bsc":
        return await send_usdc_bsc(destination_wallet, amount)
    elif chain == "trx":
        return await send_usdc_trx(destination_wallet, amount)
    elif chain == "base":
        return await send_usdc_base(destination_wallet, amount)
    elif chain == "sol":
        # pakai loop.run_in_executor biar synchronous jadi awaitable
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, send_usdc_solana, destination_wallet, amount)
    else:
        raise ValueError(f"Chain {chain} tidak didukung untuk USDC!")
