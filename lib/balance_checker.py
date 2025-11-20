# 📍 lib/balance_checker.py
import logging
import os
from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider
from solana.rpc.api import Client
from solders.pubkey import Pubkey
import asyncio

logger = logging.getLogger(__name__)

SOLANA_RPC = os.getenv("SOLANA_RPC_URL")
ETH_RPC = os.getenv("ETH_RPC_URL")
BSC_RPC = os.getenv("BSC_RPC_URL")
TRON_FULL_NODE = os.getenv("TRON_FULL_NODE")

# ===================== ETH / BSC / BNB =====================
CHAIN_RPC = {
    "eth": ETH_RPC,
    "bsc": BSC_RPC,
    "bnb": BSC_RPC,   # ✅ BNB mainnet pakai RPC BSC
}

def get_eth_bsc_balance(chain: str, wallet: str) -> float:
    rpc_url = CHAIN_RPC.get(chain.lower())
    if not rpc_url:
        logger.error(f"❌ RPC {chain} tidak ditemukan")
        return 0.0
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        balance_wei = w3.eth.get_balance(wallet)
        balance = Web3.from_wei(balance_wei, "ether")
        logger.info(f"💰 {chain.upper()} balance untuk {wallet}: {balance}")
        return float(balance)
    except Exception as e:
        logger.error(f"❌ Gagal cek {chain.upper()} wallet {wallet}: {e}")
        return 0.0

# ===================== SOLANA =====================
def get_solana_balance(wallet: str) -> float:
    try:
        client = Client(SOLANA_RPC)
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
def get_trx_balance(wallet: str) -> float:
    try:
        node_url = TRON_FULL_NODE
        client = Tron(provider=HTTPProvider(node_url))
        balance_sun = client.get_account_balance(wallet)
        balance_trx = balance_sun / 1_000_000
        logger.info(f"💰 TRX balance untuk {wallet}: {balance_trx}")
        return balance_trx
    except Exception as e:
        logger.error(f"❌ Gagal cek TRX wallet {wallet}: {e}")
        return 0.0

# ===================== WRAPPER =====================
async def check_balance(chain: str, wallet: str) -> float:
    chain = chain.lower()
    if chain in ["eth", "bsc", "bnb"]:
        return get_eth_bsc_balance(chain, wallet)
    elif chain == "sol":
        return await asyncio.to_thread(get_solana_balance, wallet)
    elif chain == "trx":
        return get_trx_balance(wallet)
    else:
        logger.error(f"❌ Chain {chain} tidak didukung")
        return 0.0
