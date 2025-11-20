# 📍 lib/eth_helper.py
import logging
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load env
load_dotenv()

ETH_RPC_URL = os.getenv("ETH_RPC_URL")
PRIVATE_KEY = os.getenv("ETH_PRIVATE_KEY")

if not ETH_RPC_URL:
    raise ValueError("❌ ETH_RPC_URL tidak ditemukan di .env")

# Init web3
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))

if not w3.is_connected():
    logger.warning("⚠️ Gagal konek ke Ethereum RPC, transaksi ETH tidak bisa dijalankan sekarang!")

if not PRIVATE_KEY:
    ADMIN_ACCOUNT = None
    logger.warning("⚠️ ETH_PRIVATE_KEY tidak ditemukan di .env")
else:
    if not PRIVATE_KEY.startswith("0x"):
        PRIVATE_KEY = "0x" + PRIVATE_KEY
    ADMIN_ACCOUNT = Account.from_key(PRIVATE_KEY)


def get_balance(address: str):
    """Cek saldo ETH dari wallet tertentu"""
    try:
        if not w3.is_connected():
            raise Exception("Ethereum RPC tidak terkoneksi!")
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_eth = w3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Saldo {address}: {balance_eth} ETH")
        return balance_eth
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None


async def send_eth(destination_wallet: str, amount_eth: float, order_id: str, user_id: int, username: str, full_name: str):
    """Kirim ETH ke wallet tujuan, helper cuma lempar exception, notif di crypto_sender.py"""
    sender_balance = None
    try:
        if not ADMIN_ACCOUNT:
            raise Exception("Private key tidak ditemukan!")

        if not w3.is_connected():
            raise Exception("Ethereum RPC tidak terkoneksi!")

        sender_address = ADMIN_ACCOUNT.address

        if destination_wallet.lower() == sender_address.lower():
            raise Exception(f"Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}")

        sender_balance = get_balance(sender_address)
        if sender_balance is None or sender_balance < amount_eth:
            raise Exception(f"Saldo tidak cukup! Saldo sekarang {sender_balance} ETH")

        nonce = w3.eth.get_transaction_count(sender_address)
        value = w3.to_wei(amount_eth, "ether")

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
        return tx_hash.hex()

    except Exception as e:
        logger.error(f"❌ Gagal kirim ETH: {e}", exc_info=True)
        # jangan panggil notif di sini
        raise e  # lempar exception supaya crypto_sender.py yang handle notif
