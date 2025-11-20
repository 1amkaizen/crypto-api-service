# 📍 lib/crypto_sender.py
import logging
import inspect
from lib.solana_helper import send_sol
from lib.usdt_helper import send_usdt
from lib.bnb_helper import send_bnb
from lib.usdc_helper import send_usdc
from lib.trx_helper import send_trx
from lib.eth_helper import send_eth
# from lib.base_helper import send_base
# from lib.ton_helper import send_ton  # <<< TAMBAH INI

logger = logging.getLogger(__name__)

# Mapping helper berdasarkan token
TOKEN_HELPERS = {
    "sol": send_sol,
    "usdt": send_usdt,   # sudah support chain (eth/bsc/trx)
    "bnb": send_bnb,
    "usdc": send_usdc,   # sudah support chain (eth/bsc/trx)
    "trx": send_trx,
    "eth": send_eth,     # native ETH
    #"base": send_base,
    #"ton": send_ton,     # <<< TAMBAH INI
}

async def send_token(token: str, chain: str, destination_wallet: str, amount: float,
                     order_id=None, user_id=None, username=None, full_name=None):
    """
    Kirim token sesuai pilihan user
    """
    token_lower = token.lower()
    send_func = TOKEN_HELPERS.get(token_lower)

    if not send_func:
        logger.error(f"❌ Token {token} belum didukung!")
        return None

    try:
        if inspect.iscoroutinefunction(send_func):
            if token_lower == "usdc":
                # 🔹 USDC → ambil chain dari parameter saja
                tx_hash = await send_func(destination_wallet, amount, chain.lower())
            elif token_lower in ["eth"]:
                # 🔹 Native chain → butuh info order + user
                tx_hash = await send_func(destination_wallet, amount, order_id, user_id, username, full_name)
            elif token_lower == "usdt":
                # 🔹 USDT → helper sudah handle chain
                tx_hash = await send_func(destination_wallet, amount, chain.lower())
            else:
                # 🔹 TRX/SOL/BNB native → tidak perlu parameter tambahan
                tx_hash = await send_func(destination_wallet, amount)
        else:
            tx_hash = send_func(destination_wallet, amount)

        if tx_hash:
            logger.info(f"✅ {token.upper()} berhasil dikirim ke {destination_wallet} di chain {chain.upper()}, tx: {tx_hash}")
        return tx_hash

    except Exception as e:
        logger.error(f"❌ Gagal kirim {token.upper()} ke {destination_wallet} di chain {chain.upper()}: {e}", exc_info=True)
        return None


async def estimate_gas_fee(
    token: str, chain: str, destination_wallet: str, amount: float
):
    """
    Estimate biaya gas untuk kirim token tertentu
    """
    token_lower = token.lower()

    # contoh dummy, nanti bisa implement per helper
    if token_lower in ["eth", "usdt", "usdc", "bnb", "sol", "trx"]:
        # misal ambil gas fee default
        gas_fee = 0.001  # atau panggil helper chain untuk estimate
        return gas_fee
    else:
        raise ValueError(f"Token {token} belum didukung untuk estimate gas")
