# 📍 File: config.py
import os
import logging
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from tronpy.keys import PrivateKey
import base58
from solders.keypair import Keypair
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Load .env
load_dotenv()

# ===== Helper =====
def get_env(name: str, default: str = None):
    value = os.getenv(name, default)
    if not value or value.strip() == "":
        logging.warning(f"ENV {name} belum di-set!")
    elif any(x in value for x in ["...", "YOUR_PROJECT_ID", "BSC_private", "HEX_PRIVATE_KEY", "path/to"]):
        logging.warning(f"ENV {name} masih placeholder: {value}")
    return value

def normalize_key(key: str):
    return key[2:] if key and key.startswith("0x") else key

def to_checksum(address: str):
    if address:
        return Web3.to_checksum_address(address.strip())
    return None

# ===== Telegram =====
BOT_TOKEN = get_env("BOT_TOKEN")
ADMIN_ID = [int(x.strip()) for x in get_env("ADMIN_ID", "").split(",") if x.strip().isdigit()]
ADMIN_USERNAME = get_env("ADMIN_USERNAME")
BOT_USERNAME = get_env("BOT_USERNAME")

# Link channel VIP
CHANNEL_VIP_LINK = get_env("CHANNEL_VIP_LINK")

# ===== Supabase =====
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")

# ===== Midtrans =====
MIDTRANS_SERVER_KEY = get_env("MIDTRANS_SERVER_KEY")
MIDTRANS_IS_PRODUCTION = get_env("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"
MIDTRANS_DISBURSEMENT_KEY = get_env("MIDTRANS_DISBURSEMENT_KEY")

# ===== Solana =====
SOLANA_RPC_URL = get_env("SOLANA_RPC_URL")
SOLANA_RPC_WSS = get_env("SOLANA_RPC_WSS")
SOLANA_PRIVATE_KEY = get_env("SOLANA_PRIVATE_KEY")
SOLANA_ADMIN_WALLET = get_env("SOLANA_ADMIN_WALLET")

# 🔑 Keypair admin Solana (buat sign tx)
SOL_ACCOUNT = Keypair.from_bytes(base58.b58decode(SOLANA_PRIVATE_KEY)) if SOLANA_PRIVATE_KEY else None

# 🪙 Token address di Solana
SOL_USDT_ADDRESS = get_env("SOL_USDT_ADDRESS")  # alamat mint USDT SPL
SOL_USDC_ADDRESS = get_env("SOL_USDC_ADDRESS")  # alamat mint USDC SPL

# ===== Coingecko =====
COINGECKO_API = get_env("COINGECKO_API")

# ===== Backend =====
BACKEND_BASE_URL = get_env("BACKEND_BASE_URL")

# ===== Ecer =====
ECER_MAINTENANCE = get_env("ECER_MAINTENANCE", "false").lower() == "true"

# ===== Ethereum =====
ETH_RPC_URL = get_env("ETH_RPC_URL")
ETH_PRIVATE_KEY = normalize_key(get_env("ETH_PRIVATE_KEY"))
ETH_ACCOUNT = Account.from_key("0x" + ETH_PRIVATE_KEY) if ETH_PRIVATE_KEY else None
ETH_CHAIN_ID = int(get_env("ETH_CHAIN_ID", 1))

ETH_USDT_ADDRESS = to_checksum(get_env("ETH_USDT_ADDRESS"))
ETH_USDC_ADDRESS = to_checksum(get_env("ETH_USDC_ADDRESS"))

# ===== BSC =====
BSC_RPC_URL = get_env("BSC_RPC_URL")
BSC_PRIVATE_KEY = normalize_key(get_env("BSC_PRIVATE_KEY"))
BSC_ACCOUNT = Account.from_key("0x" + BSC_PRIVATE_KEY) if BSC_PRIVATE_KEY else None

BSC_USDT_ADDRESS = to_checksum(get_env("BSC_USDT_ADDRESS"))
BSC_USDC_ADDRESS = to_checksum(get_env("BSC_USDC_ADDRESS"))
# ambil chain ID, default 56 (BSC mainnet) kalau .env ga ada
BSC_CHAIN_ID = int(get_env("BSC_CHAIN_ID", 56))

# ===== Tron =====
TRON_FULL_NODE = get_env("TRON_FULL_NODE")
TRON_PRIVATE_KEY = normalize_key(get_env("TRON_PRIVATE_KEY"))
TRON_ACCOUNT = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY)) if TRON_PRIVATE_KEY else None

TRC20_USDT_ADDRESS = get_env("TRC20_USDT_ADDRESS")
TRC20_USDC_ADDRESS = get_env("TRC20_USDC_ADDRESS")

# ===== Base (Coinbase L2) =====
BASE_RPC_URL = get_env("BASE_RPC_URL")
BASE_PRIVATE_KEY = normalize_key(get_env("BASE_PRIVATE_KEY"))
BASE_ACCOUNT = Account.from_key("0x" + BASE_PRIVATE_KEY) if BASE_PRIVATE_KEY else None

BASE_USDT_ADDRESS = to_checksum(get_env("BASE_USDT_ADDRESS"))
BASE_USDC_ADDRESS = to_checksum(get_env("BASE_USDC_ADDRESS"))


# ===== Logging overview =====
logging.info(f"ETH_ACCOUNT: {ETH_ACCOUNT.address if ETH_ACCOUNT else None}")
logging.info(f"BSC_ACCOUNT: {BSC_ACCOUNT.address if BSC_ACCOUNT else None}")
logging.info(f"TRON_ACCOUNT: {TRON_ACCOUNT.public_key.to_base58check_address() if TRON_ACCOUNT else None}")
