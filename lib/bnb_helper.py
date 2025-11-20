# 📍 lib/bnb_helper.py
import logging
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from datetime import datetime

logger = logging.getLogger(__name__)

# Load env
load_dotenv()

BSC_RPC_URL = os.getenv("BSC_RPC_URL")
PRIVATE_KEY = os.getenv("BSC_PRIVATE_KEY")
BSC_CHAIN_ID = int(os.getenv("BSC_CHAIN_ID", "56"))  # default mainnet

if not BSC_RPC_URL:
    raise ValueError("❌ BSC_RPC_URL tidak ditemukan di .env")

# Init web3
w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))

if not w3.is_connected():
    logger.warning("⚠️ Gagal konek ke BSC RPC, transaksi BNB tidak bisa dijalankan sekarang!")

if not PRIVATE_KEY:
    ADMIN_ACCOUNT = None
    logger.warning("⚠️ BSC_PRIVATE_KEY tidak ditemukan di .env")
else:
    if not PRIVATE_KEY.startswith("0x"):
        PRIVATE_KEY = "0x" + PRIVATE_KEY
    ADMIN_ACCOUNT = Account.from_key(PRIVATE_KEY)
    logger.info(f"🔑 Admin BNB wallet siap: {ADMIN_ACCOUNT.address}")


def get_balance(address: str):
    """Cek saldo BNB dari wallet tertentu"""
    try:
        if not w3.is_connected():
            raise Exception("BSC RPC tidak terkoneksi!")
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_bnb = w3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Saldo {address}: {balance_bnb} BNB")
        return balance_bnb
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None


async def send_bnb(destination_wallet: str, amount_bnb: float, order_id=None, user_id=None, username=None):
    """
    📌 Kirim BNB ke wallet tujuan dari admin wallet (Mainnet/Testnet)
    """
    try:
        if not ADMIN_ACCOUNT:
            raise Exception("Private key tidak ditemukan!")
        if not w3.is_connected():
            raise Exception("BSC RPC tidak terkoneksi!")

        sender_address = ADMIN_ACCOUNT.address

        if destination_wallet.lower() == sender_address.lower():
            raise Exception(f"Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}")

        sender_balance = get_balance(sender_address)
        if sender_balance is None or sender_balance < amount_bnb:
            raise Exception(f"Saldo tidak cukup! Saldo sekarang {sender_balance} BNB")

        nonce = w3.eth.get_transaction_count(sender_address)
        value = w3.to_wei(amount_bnb, "ether")

        tx = {
            "nonce": nonce,
            "to": Web3.to_checksum_address(destination_wallet),
            "value": value,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "chainId": BSC_CHAIN_ID,
        }

        logger.info(
            f"🚀 Kirim BNB ke {destination_wallet} | amount={amount_bnb} | "
            f"order_id={order_id} | user_id={user_id} | username={username}"
        )

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        # Tentukan explorer URL sesuai chain
        explorer_base = (
            "https://bscscan.com" if BSC_CHAIN_ID == 56 else "https://testnet.bscscan.com"
        )
        tx_link = f"{explorer_base}/tx/{tx_hash_hex}"

        logger.info(f"✅ BNB berhasil dikirim! tx_hash: {tx_hash_hex}")
        logger.info(f"🔗 Lihat transaksi di BscScan: {tx_link}")

        return tx_hash_hex

    except Exception as e:
        logger.error(f"❌ Gagal kirim BNB: {e}", exc_info=True)
        return None

async def check_balance(wallet_address: str):
    """Wrapper async untuk get_balance supaya bisa await di handler"""
    return get_balance(wallet_address)