# 📍 lib/balance_checker.py
import logging
from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider
from solana.rpc.api import Client
from solders.pubkey import Pubkey
import asyncio

logger = logging.getLogger(__name__)


# ===================== ETH / BSC / BNB =====================
def get_eth_bsc_balance(rpc_url: str, wallet: str) -> float:
    if not rpc_url:
        logger.error("❌ RPC tidak diberikan")
        return 0.0
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        balance_wei = w3.eth.get_balance(wallet)
        balance = Web3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Balance untuk {wallet}: {balance}")
        return float(balance)
    except Exception as e:
        logger.error(f"❌ Gagal cek wallet {wallet}: {e}")
        return 0.0


# ===================== SOLANA =====================
def get_solana_balance(rpc_url: str, wallet: str) -> float:
    if not rpc_url:
        logger.error("❌ RPC tidak diberikan")
        return 0.0
    try:
        client = Client(rpc_url)
        pubkey = Pubkey.from_string(wallet)
        resp = client.get_balance(pubkey)
        lamports = resp.value
        sol = lamports / 1_000_000_000
        logger.info(f"💰 SOL balance untuk {wallet}: {sol}")
        return sol
    except Exception as e:
        logger.error(f"❌ Gagal cek SOL wallet {wallet}: {e}", exc_info=True)
        return 0.0


# ===================== TRON =====================
def get_trx_balance(node_url: str, wallet: str) -> float:
    if not node_url:
        logger.error("❌ Node URL tidak diberikan")
        return 0.0
    try:
        client = Tron(provider=HTTPProvider(node_url))
        balance_sun = client.get_account_balance(wallet)
        balance_trx = balance_sun / 1_000_000
        logger.info(f"💰 TRX balance untuk {wallet}: {balance_trx}")
        return balance_trx
    except Exception as e:
        logger.error(f"❌ Gagal cek TRX wallet {wallet}: {e}")
        return 0.0


# ===================== WRAPPER =====================
async def check_balance(chain: str, wallet: str, rpc_url: str) -> float:
    chain = chain.lower()
    if chain in ["eth", "bsc", "bnb"]:
        return get_eth_bsc_balance(rpc_url, wallet)
    elif chain == "sol":
        return await asyncio.to_thread(get_solana_balance, rpc_url, wallet)
    elif chain == "trx":
        return get_trx_balance(rpc_url, wallet)
    else:
        logger.error(f"❌ Chain {chain} tidak didukung")
        return 0.0
