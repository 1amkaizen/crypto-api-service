# 📍 lib/helpers/usdt/bsc.py
import logging
import time
from web3 import Web3
from config import BSC_ACCOUNT, BSC_RPC_URL, BSC_USDT_ADDRESS, BSC_CHAIN_ID  

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Setup client BSC
w3_bsc = Web3(Web3.HTTPProvider(BSC_RPC_URL)) if BSC_RPC_URL else None

# ERC20 minimal ABI
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

def get_usdt_balance(wallet_address: str, retries: int = 3) -> float:
    """
    Cek saldo USDT (BEP20) dari wallet_address, dengan retry bila gagal.
    """
    if not w3_bsc:
        logger.error("❌ BSC RPC tidak tersedia")
        return 0.0

    contract = w3_bsc.eth.contract(address=BSC_USDT_ADDRESS, abi=ERC20_ABI)

    # ambil decimals
    try:
        decimals = contract.functions.decimals().call()
    except Exception:
        logger.warning("⚠️ Gagal baca decimals, pakai default 18 (BSC USDT)")
        decimals = 18

    attempt = 0
    while attempt < retries:
        try:
            balance_raw = contract.functions.balanceOf(wallet_address).call()
            balance = balance_raw / (10 ** decimals)
            logger.info(f"💰 Saldo USDT {wallet_address}: {balance} USDT")
            return balance
        except Exception as e:
            logger.warning(f"⚠️ Gagal cek saldo (attempt {attempt+1}/{retries}): {e}")
            attempt += 1
            time.sleep(1)

    logger.error(f"❌ Gagal cek saldo USDT BSC setelah {retries} percobaan, return 0")
    return 0.0


async def send_usdt_bsc(destination_wallet: str, amount: float):
    if not w3_bsc or not BSC_ACCOUNT:
        logger.error("❌ BSC RPC atau account tidak tersedia")
        return None

    contract = w3_bsc.eth.contract(address=BSC_USDT_ADDRESS, abi=ERC20_ABI)

    # ambil decimals
    try:
        decimals = contract.functions.decimals().call()
    except Exception:
        logger.warning("⚠️ Gagal baca decimals, pakai default 18 (BSC USDT)")
        decimals = 18

    value = int(amount * (10 ** decimals))

    # log saldo sebelum kirim
    get_usdt_balance(BSC_ACCOUNT.address)
    get_usdt_balance(destination_wallet)

    try:
        # ambil nonce pending
        nonce = w3_bsc.eth.get_transaction_count(BSC_ACCOUNT.address, "pending")

        # gas price aman
        current_gas_price = w3_bsc.eth.gas_price
        safe_gas_price = int(current_gas_price * 1.2)

        tx = contract.functions.transfer(
            Web3.to_checksum_address(destination_wallet),
            value
        ).build_transaction({
            "chainId": BSC_CHAIN_ID,
            "gas": 100000,
            "gasPrice": safe_gas_price,
            "nonce": nonce,
        })

        signed_tx = w3_bsc.eth.account.sign_transaction(tx, BSC_ACCOUNT.key)
        tx_hash = w3_bsc.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"🕓 Menunggu konfirmasi transaksi {tx_hash.hex()}...")

        receipt = w3_bsc.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        if receipt.status == 1:
            logger.info(f"✅ USDT BEP20 berhasil masuk ke {destination_wallet}, tx_hash={tx_hash.hex()}")
            # log saldo setelah kirim
            get_usdt_balance(BSC_ACCOUNT.address)
            get_usdt_balance(destination_wallet)
            return tx_hash.hex()
        else:
            logger.error(f"❌ Transaksi gagal masuk blockchain: {tx_hash.hex()}")
            return None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT BEP20: {e}", exc_info=True)
        return None
