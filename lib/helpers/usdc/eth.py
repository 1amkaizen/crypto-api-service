# 📍 lib/helpers/usdc/eth.py
import logging
import asyncio
from web3 import Web3
from config import ETH_ACCOUNT, ETH_RPC_URL, ETH_USDC_ADDRESS, ETH_CHAIN_ID

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ===== Client Ethereum =====
w3_eth = Web3(Web3.HTTPProvider(ETH_RPC_URL)) if ETH_RPC_URL else None

# ===== ERC20 ABI =====
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

# ===== Fungsi cek saldo USDC =====
def get_usdc_balance(wallet_address: str) -> float:
    try:
        if not w3_eth:
            raise Exception("Ethereum RPC tidak tersedia")
        contract = w3_eth.eth.contract(address=ETH_USDC_ADDRESS, abi=ERC20_ABI)
        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDC)")
            decimals = 6
        balance = contract.functions.balanceOf(wallet_address).call() / (10 ** decimals)
        logger.info(f"💰 Saldo USDC {wallet_address}: {balance} USDC")
        return balance
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDC: {e}", exc_info=True)
        return 0.0

# ===== Async polling untuk receipt =====
async def wait_tx_receipt_async(tx_hash: str, poll_interval: int = 5, timeout: int = 180):
    await asyncio.sleep(2)  # delay awal supaya node register tx
    start = asyncio.get_event_loop().time()
    while True:
        try:
            receipt = w3_eth.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except Exception as e:
            # catch TransactionNotFound, terus retry
            if "not found" not in str(e):
                raise
        if asyncio.get_event_loop().time() - start > timeout:
            raise TimeoutError(f"⏳ Timeout tunggu receipt tx {tx_hash}")
        await asyncio.sleep(poll_interval)

# ===== Fungsi Kirim USDC ERC20 aman =====
async def send_usdc_eth(destination_wallet: str, amount: float):
    try:
        if not w3_eth or not ETH_ACCOUNT:
            raise Exception("Ethereum RPC atau account tidak tersedia")

        contract = w3_eth.eth.contract(address=ETH_USDC_ADDRESS, abi=ERC20_ABI)

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDC)")
            decimals = 6

        # log saldo sebelum kirim
        get_usdc_balance(ETH_ACCOUNT.address)
        get_usdc_balance(destination_wallet)

        # cek balance cukup
        balance_usdc = contract.functions.balanceOf(ETH_ACCOUNT.address).call() / (10 ** decimals)
        if amount > balance_usdc:
            raise Exception(f"USDC balance tidak cukup: {balance_usdc} < {amount}")

        value = int(amount * (10 ** decimals))
        nonce = w3_eth.eth.get_transaction_count(ETH_ACCOUNT.address, "pending")

        # build tx final
        tx = contract.functions.transfer(
            Web3.to_checksum_address(destination_wallet),
            value
        ).build_transaction({
            "chainId": ETH_CHAIN_ID,
            "gas": 100000,
            "gasPrice": int(w3_eth.eth.gas_price * 1.2),  # gas aman +20%
            "nonce": nonce,
            "from": ETH_ACCOUNT.address
        })

        signed_tx = w3_eth.eth.account.sign_transaction(tx, ETH_ACCOUNT.key)
        tx_hash = w3_eth.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"🕓 Menunggu konfirmasi transaksi {tx_hash.hex()}...")

        receipt = await wait_tx_receipt_async(tx_hash.hex())
        if receipt.status == 1:
            logger.info(f"✅ USDC ERC20 berhasil masuk ke {destination_wallet}, tx_hash={tx_hash.hex()}")
            # log saldo setelah kirim
            get_usdc_balance(ETH_ACCOUNT.address)
            get_usdc_balance(destination_wallet)
            return tx_hash.hex()
        else:
            logger.error(f"❌ Transaksi gagal masuk blockchain: {tx_hash.hex()}")
            return None

    except Exception as e:
        if hasattr(e, 'args') and len(e.args) > 0:
            logger.error(f"❌ Contract revert: {e.args[0]}", exc_info=True)
        else:
            logger.error(f"❌ Gagal kirim USDC ERC20: {e}", exc_info=True)
        return None
