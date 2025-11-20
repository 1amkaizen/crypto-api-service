# 📍 lib/helpers/usdc/trx.py

import logging
import time
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from tronpy.exceptions import TransactionNotFound
from config import TRON_FULL_NODE, TRON_PRIVATE_KEY, TRC20_USDC_ADDRESS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ABI TRC20 standar
TRC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "transfer", "outputs": [{"name": "", "type": "bool"}],
     "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "payable": False, "stateMutability": "view", "type": "function"},
]

# Setup client TRX
client = Tron(HTTPProvider(TRON_FULL_NODE)) if TRON_FULL_NODE else None
account = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY)) if TRON_PRIVATE_KEY else None
TRON_ADDRESS = account.public_key.to_base58check_address() if account else None


def get_usdc_balance(wallet_address: str) -> float:
    """
    Cek saldo USDC (TRC20) dari wallet_address
    """
    try:
        if not client:
            raise Exception("Tron node tidak tersedia")

        contract = client.get_contract(TRC20_USDC_ADDRESS)

        try:
            decimals = contract.functions.decimals()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDC)")
            decimals = 6

        balance_raw = contract.functions.balanceOf(wallet_address)
        balance = balance_raw / (10 ** decimals)

        logger.info(f"💰 Saldo USDC {wallet_address}: {balance} USDC")
        return balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDC: {e}", exc_info=True)
        return 0.0


# 📍 lib/helpers/usdc/trx.py

async def send_usdc_trx(destination_wallet: str, amount: float):
    """
    Kirim USDC TRC20 ke wallet tujuan dengan logging lengkap, retry, dan pengecekan energy/saldo.
    """
    try:
        if not client or not account:
            raise Exception("Tron node atau private key tidak tersedia")

        # Ambil kontrak USDC
        contract = client.get_contract(TRC20_USDC_ADDRESS)

        # Ambil decimals
        try:
            decimals = contract.functions.decimals()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDC)")
            decimals = 6

        value = int(amount * (10 ** decimals))

        # Cek saldo USDC admin
        admin_balance = get_usdc_balance(TRON_ADDRESS)
        if admin_balance < amount:
            raise Exception(f"Saldo USDC admin tidak cukup: {admin_balance} < {amount}")

        # Cek TRX untuk energy
        admin_trx_balance = client.get_account(TRON_ADDRESS)["balance"] / 1_000_000
        if admin_trx_balance < 0.1:  # threshold minimal
            raise Exception(f"Saldo TRX admin terlalu rendah untuk bayar fee: {admin_trx_balance} TRX")

        # Build & sign transaksi
        txn = (
            contract.functions.transfer(destination_wallet, value)
            .with_owner(TRON_ADDRESS)
            .build()
            .sign(account)
        )

        tx_result = txn.broadcast()
        tx_hash = tx_result["txid"]
        logger.info(f"🕓 Menunggu konfirmasi transaksi TRX {tx_hash}...")

        # Retry cek transaksi
        receipt = None
        for i in range(10):
            try:
                receipt = client.get_transaction_info(tx_hash)
                break
            except TransactionNotFound:
                logger.info(f"⏳ Transaksi {tx_hash} belum masuk block, retry {i+1}/10...")
                time.sleep(3)

        if not receipt:
            logger.error(f"❌ Transaksi {tx_hash} tidak ditemukan setelah 30 detik")
            return None

        # Cek hasil transaksi
        result = receipt.get("receipt", {}).get("result")
        if result == "SUCCESS":
            logger.info(f"✅ USDC berhasil dikirim ke {destination_wallet}, tx_hash={tx_hash}")
            # log saldo setelah kirim
            get_usdc_balance(TRON_ADDRESS)
            get_usdc_balance(destination_wallet)
            return tx_hash
        else:
            err_msg = receipt.get("receipt", {}).get("resultMessage", "Unknown error")
            logger.error(f"❌ Transaksi gagal: {tx_hash}, reason={err_msg}, full_receipt={receipt}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDC: {e}", exc_info=True)
        return None
