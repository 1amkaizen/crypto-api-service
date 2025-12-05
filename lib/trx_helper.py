# 📍 lib/trx_helper.py
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

logger = logging.getLogger(__name__)


async def send_trx(
    destination_wallet: str,
    amount_trx: float,
    rpc_url: str = None,  # 🔹 endpoint kirim rpc_url
    private_key: str = None,  # 🔹 endpoint kirim private_key
    order_id: str = None,
    user_id: int = None,
    username: str = None,
    full_name: str = None,
) -> str:
    """
    📌 Kirim TRX ke wallet tujuan
    rpc_url & private_key dikirim dari endpoint
    """
    if not rpc_url:
        raise ValueError("❌ RPC URL harus diberikan!")
    if not private_key:
        raise ValueError("❌ private key harus diberikan!")

    try:
        client = Tron(HTTPProvider(rpc_url))

        # Load admin key
        admin_key = PrivateKey(bytes.fromhex(private_key.replace("0x", "")))
        admin_address = admin_key.public_key.to_base58check_address()
        logger.info(f"🔑 Admin TRX wallet siap: {admin_address}")

        if destination_wallet == admin_address:
            raise Exception(
                f"Destination sama dengan source! Batal kirim: {destination_wallet}"
            )

        # Cek saldo
        balance = client.get_account_balance(admin_address)
        logger.info(
            f"💰 Saldo admin TRX: {balance} TRX | Admin address: {admin_address}"
        )
        if balance < amount_trx:
            raise Exception("❌ Saldo TRX admin tidak cukup!")

        logger.info(
            f"🚀 Kirim TRX ke {destination_wallet} | amount={amount_trx} | "
            f"order_id={order_id} | user_id={user_id} | username={username}"
        )

        amount_sun = int(amount_trx * 1_000_000)  # 1 TRX = 1_000_000 SUN

        # Build, sign & broadcast transaction
        txn = (
            client.trx.transfer(admin_address, destination_wallet, amount_sun)
            .build()
            .sign(admin_key)
        )
        result = txn.broadcast().wait(timeout=30)
        logger.info(f"📦 Response dari jaringan TRX: {result}")

        if isinstance(result, dict):
            tx_hash = result.get("txid") or result.get("id")
            if tx_hash:
                tronscan_link = f"https://tronscan.org/#/transaction/{tx_hash}"
                logger.info(f"✅ TRX berhasil dikirim! tx_hash: {tx_hash}")
                logger.info(f"🔗 Lihat transaksi di TRONSCAN: {tronscan_link}")
                return tx_hash
        raise Exception(f"❌ TRX gagal / response invalid: {result}")

    except Exception as e:
        logger.error(f"❌ Gagal kirim TRX: {e}", exc_info=True)
        raise e  # crypto_sender.py yang handle notif


def get_balance(address: str, rpc_url: str) -> float:
    """
    📌 Cek saldo TRX dari wallet tertentu
    rpc_url dikirim dari endpoint
    """
    if not rpc_url:
        raise ValueError("❌ RPC URL harus diberikan!")
    try:
        client = Tron(HTTPProvider(rpc_url))
        balance = client.get_account_balance(address)
        logger.info(f"💰 Saldo {address}: {balance} TRX")
        return balance
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None
