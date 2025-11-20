# 📍 lib/helpers/usdc/base.py
import logging
import time
import asyncio
from functools import partial
from web3 import Web3
from config import BASE_ACCOUNT, BASE_RPC_URL, BASE_USDC_ADDRESS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Setup client Base
w3_base = Web3(Web3.HTTPProvider(BASE_RPC_URL))
account_address = Web3.to_checksum_address(BASE_ACCOUNT.address)
private_key = BASE_ACCOUNT.key

# ERC20 ABI minimal
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "transfer", "outputs": [{"name": "", "type": "bool"}],
     "payable": False, "stateMutability": "nonpayable", "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "payable": False, "stateMutability": "view", "type": "function"},
]

contract = w3_base.eth.contract(address=BASE_USDC_ADDRESS, abi=ERC20_ABI)


def get_usdc_balance(wallet_address: str) -> float:
    """Cek saldo USDC Base"""
    try:
        decimals = contract.functions.decimals().call()
        balance_raw = contract.functions.balanceOf(wallet_address).call()
        balance = balance_raw / (10 ** decimals)
        logger.info(f"💰 Saldo USDC Base {wallet_address}: {balance}")
        return balance
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo Base USDC: {e}", exc_info=True)
        return 0.0


def send_usdc_base_sync(destination_wallet: str, amount: float):
    """Kirim USDC Base (sync, robust)"""
    try:
        decimals = contract.functions.decimals().call()
        value = int(amount * (10 ** decimals))
        nonce = w3_base.eth.get_transaction_count(account_address, 'pending')
        safe_gas_price = int(w3_base.eth.gas_price * 1.2)

        txn = contract.functions.transfer(destination_wallet, value).build_transaction({
            "from": account_address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": safe_gas_price,
            "chainId": w3_base.eth.chain_id,
        })

        signed_txn = w3_base.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3_base.eth.send_raw_transaction(signed_txn.raw_transaction)
        logger.info(f"🕓 Menunggu konfirmasi transaksi {tx_hash.hex()}...")

        # retry loop sampai mined atau timeout 180 detik
        receipt = None
        start_time = time.time()
        while time.time() - start_time < 180:
            try:
                receipt = w3_base.eth.get_transaction_receipt(tx_hash)
                break
            except Exception:
                logger.info("⏳ Transaksi belum mined, tunggu 5 detik...")
                time.sleep(5)

        if not receipt:
            logger.error(f"❌ Transaksi {tx_hash.hex()} tidak ditemukan dalam 180 detik")
            return None

        if receipt.status == 1:
            logger.info(f"✅ Token berhasil dikirim ke {destination_wallet}, tx_hash={tx_hash.hex()}")
            get_usdc_balance(account_address)
            get_usdc_balance(destination_wallet)
            return tx_hash.hex()
        else:
            logger.error(f"❌ Transaksi gagal: {tx_hash.hex()}, receipt={receipt}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDC Base: {e}", exc_info=True)
        return None


async def send_usdc_base(destination_wallet: str, amount: float):
    """Kirim USDC Base (async-safe)"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(send_usdc_base_sync, destination_wallet, amount))
