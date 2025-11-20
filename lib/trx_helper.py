# 📍 lib/trx_helper.py
import logging
import os
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

logger = logging.getLogger(__name__)

# === TRON CLIENT & ADMIN ===
TRON_FULL_NODE = os.getenv("TRON_FULL_NODE")  # contoh: "https://api.trongrid.io"
TRON_PRIVATE_KEY = os.getenv("TRON_PRIVATE_KEY")

if not TRON_PRIVATE_KEY:
    raise ValueError("❌ TRON_PRIVATE_KEY belum di-set di .env")

if not TRON_FULL_NODE:
    raise ValueError("❌ TRON_FULL_NODE belum di-set di .env, wajib untuk mainnet")

# Inisialisasi client Tron (versi lama, tanpa api_key)
client = Tron(HTTPProvider(TRON_FULL_NODE))

# Load admin key
try:
    admin_key = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY))
    admin_address = admin_key.public_key.to_base58check_address()
    logger.info(f"🔑 Admin TRX wallet siap: {admin_address}")
except Exception as e:
    logger.error(f"❌ TRON_PRIVATE_KEY salah: {e}")
    admin_key = None
    admin_address = None


async def send_trx(
    destination_wallet: str,
    amount_trx: float,
    order_id: str = None,
    user_id: int = None,
    username: str = None,
    full_name: str = None
) -> str:
    """
    📌 Kirim TRX ke wallet tujuan dari admin wallet (Mainnet/Testnet)
    Compatible tronpy 0.6.1
    """
    if not admin_key or not admin_address:
        logger.error("❌ TRON_PRIVATE_KEY belum valid, batal kirim TRX")
        return None

    if destination_wallet == admin_address:
        logger.warning(f"❌ Destination sama dengan source! Batal kirim: {destination_wallet}")
        return None

    try:
        # --- CEK SALDO ADMIN TERLEBIH DAHULU ---
        balance = client.get_account_balance(admin_address)
        logger.info(f"💰 Saldo admin TRX: {balance} TRX | Admin address: {admin_address}")

        if balance < amount_trx:
            logger.error("❌ Saldo TRX admin tidak cukup!")
            return None

        logger.info(
            f"🚀 Kirim TRX ke {destination_wallet} | amount={amount_trx} | "
            f"order_id={order_id} | user_id={user_id} | username={username}"
        )

        amount_sun = int(amount_trx * 1_000_000)  # 1 TRX = 1_000_000 SUN

        # Build & sign transaction
        txn = client.trx.transfer(admin_address, destination_wallet, amount_sun).build().sign(admin_key)
        logger.info("📝 Transaksi dibangun dan ditandatangani, kirim ke jaringan...")

        # Broadcast dan tunggu konfirmasi
        result = txn.broadcast().wait(timeout=30)
        logger.info(f"📦 Response dari jaringan TRX: {result}")

        if isinstance(result, dict):
            tx_hash = result.get('txid') or result.get('id')
            if tx_hash:
                tronscan_link = f"https://tronscan.org/#/transaction/{tx_hash}"
                logger.info(f"✅ TRX berhasil dikirim! tx_hash: {tx_hash}")
                logger.info(f"🔗 Lihat transaksi di TRONSCAN: {tronscan_link}")
                return tx_hash
            else:
                logger.error(f"❌ TRX gagal / txid kosong, response: {result}")
                return None
        else:
            logger.error(f"❌ TRX gagal dikirim / response invalid: {result}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim TRX: {e}", exc_info=True)
        return None


def get_balance(address: str) -> float:
    """
    📌 Cek saldo TRX dari wallet tertentu
    """
    try:
        balance = client.get_account_balance(address)
        logger.info(f"💰 Saldo {address}: {balance} TRX")
        return balance
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None