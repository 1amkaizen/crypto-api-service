# 📍 lib/base_helper.py
import logging
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load env
load_dotenv()

BASE_RPC_URL = os.getenv("BASE_RPC_URL")
PRIVATE_KEY = os.getenv("BASE_PRIVATE_KEY")

if not BASE_RPC_URL:
    raise ValueError("❌ BASE_RPC_URL tidak ditemukan di .env")

# Init web3
w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

if not w3.is_connected():
    logger.warning("⚠️ Gagal konek ke BASE RPC, transaksi BASE tidak bisa dijalankan sekarang!")

if not PRIVATE_KEY:
    ADMIN_ACCOUNT = None
    logger.warning("⚠️ BASE_PRIVATE_KEY tidak ditemukan di .env")
else:
    if not PRIVATE_KEY.startswith("0x"):
        PRIVATE_KEY = "0x" + PRIVATE_KEY
    ADMIN_ACCOUNT = Account.from_key(PRIVATE_KEY)


def get_balance(address: str):
    """Cek saldo BASE (native) dari wallet tertentu"""
    try:
        if not w3.is_connected():
            raise Exception("BASE RPC tidak terkoneksi!")
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_base = w3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Saldo {address}: {balance_base} BASE")
        return balance_base
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None


async def send_base(destination_wallet: str, amount_base: float, order_id: str, user_id: int, username: str, full_name: str):
    """Kirim BASE ke wallet tujuan, helper lempar exception, notif di crypto_sender.py"""
    sender_balance = None
    try:
        if not ADMIN_ACCOUNT:
            raise Exception("Private key tidak ditemukan!")

        if not w3.is_connected():
            raise Exception("BASE RPC tidak terkoneksi!")

        sender_address = ADMIN_ACCOUNT.address

        if destination_wallet.lower() == sender_address.lower():
            raise Exception(f"Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}")

        sender_balance = get_balance(sender_address)
        if sender_balance is None or sender_balance < amount_base:
            raise Exception(f"Saldo tidak cukup! Saldo sekarang {sender_balance} BASE")

        nonce = w3.eth.get_transaction_count(sender_address)
        value = w3.to_wei(amount_base, "ether")

        tx = {
            "nonce": nonce,
            "to": Web3.to_checksum_address(destination_wallet),
            "value": value,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"✅ Kirim {amount_base} BASE ke {destination_wallet}, tx_hash: {tx_hash.hex()}")
        return tx_hash.hex()

    except Exception as e:
        logger.error(f"❌ Gagal kirim BASE: {e}", exc_info=True)
        raise e  # lempar exception supaya crypto_sender.py yang handle notif
