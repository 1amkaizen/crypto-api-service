# 📍 lib/helpers/usdt/trx.py

import logging
import time
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from tronpy.exceptions import TransactionNotFound
from config import TRON_FULL_NODE, TRON_PRIVATE_KEY, TRC20_USDT_ADDRESS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ABI hasil compile kontrak MyToken.sol
TRC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "transfer", "outputs": [{"name": "", "type": "bool"}],
     "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}],
     "payable": False, "stateMutability": "view", "type": "function"},
]

# Setup client TRX
client = Tron(HTTPProvider(TRON_FULL_NODE)) if TRON_FULL_NODE else None
account = PrivateKey(bytes.fromhex(TRON_PRIVATE_KEY)) if TRON_PRIVATE_KEY else None
TRON_ADDRESS = account.public_key.to_base58check_address() if account else None


def get_usdt_balance(wallet_address: str) -> float:
    """
    Cek saldo USDT (TRC20) dari wallet_address
    """
    try:
        if not client:
            raise Exception("Tron node tidak tersedia")

        contract = client.get_contract(TRC20_USDT_ADDRESS)

        try:
            decimals = contract.functions.decimals()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDT)")
            decimals = 6

        balance_raw = contract.functions.balanceOf(wallet_address)
        balance = balance_raw / (10 ** decimals)

        logger.info(f"💰 Saldo USDT {wallet_address}: {balance} USDT")
        return balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDT: {e}", exc_info=True)
        return 0.0


async def send_usdt_trx(destination_wallet: str, amount: float):
    try:
        if not client or not account:
            raise Exception("Tron node atau private key tidak tersedia")

        contract = client.get_contract(TRC20_USDT_ADDRESS)

        try:
            decimals = contract.functions.decimals()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDT)")
            decimals = 6

        value = int(amount * (10 ** decimals))

        txn = (
            contract.functions.transfer(destination_wallet, value)
            .with_owner(TRON_ADDRESS)
            .build()
            .sign(account)
        )

        tx_result = txn.broadcast()
        tx_hash = tx_result["txid"]
        logger.info(f"🕓 Menunggu konfirmasi transaksi TRX {tx_hash}...")

        # === retry loop: cek sampai trx ketemu atau timeout 30 detik ===
        receipt = None
        for i in range(10):  # maksimal 10x cek
            try:
                receipt = client.get_transaction_info(tx_hash)
                break  # kalau ketemu, stop loop
            except TransactionNotFound:
                logger.info(f"⏳ Transaksi {tx_hash} belum masuk block, retry {i+1}/10...")
                time.sleep(3)

        if not receipt:
            logger.error(f"❌ Transaksi {tx_hash} tidak ditemukan setelah 30 detik")
            return None

        if receipt.get("receipt", {}).get("result") == "SUCCESS":
            logger.info(f"✅ Token berhasil dikirim ke {destination_wallet}, tx_hash={tx_hash}")
            # log saldo setelah kirim
            get_usdt_balance(TRON_ADDRESS)
            get_usdt_balance(destination_wallet)
            return tx_hash
        else:
            logger.error(f"❌ Transaksi gagal: {tx_hash}, receipt={receipt}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim token: {e}", exc_info=True)
        return None
