# 📍 lib/helpers/usdt/eth.py
import logging
from web3 import Web3
from config import ETH_ACCOUNT, ETH_RPC_URL, ETH_USDT_ADDRESS, ETH_CHAIN_ID

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Setup client ETH
w3_eth = Web3(Web3.HTTPProvider(ETH_RPC_URL)) if ETH_RPC_URL else None

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

def get_usdt_balance(wallet_address: str) -> float:
    """
    Cek saldo USDT (ERC20) dari wallet_address
    """
    try:
        if not w3_eth:
            raise Exception("Ethereum RPC tidak tersedia")

        contract = w3_eth.eth.contract(address=ETH_USDT_ADDRESS, abi=ERC20_ABI)

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDT)")
            decimals = 6

        balance_raw = contract.functions.balanceOf(wallet_address).call()
        balance = balance_raw / (10 ** decimals)
        logger.info(f"💰 Saldo USDT {wallet_address}: {balance} USDT")
        return balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDT: {e}", exc_info=True)
        return 0.0


async def send_usdt_eth(destination_wallet: str, amount: float):
    try:
        if not w3_eth or not ETH_ACCOUNT:
            raise Exception("Ethereum RPC atau account tidak tersedia")

        contract = w3_eth.eth.contract(address=ETH_USDT_ADDRESS, abi=ERC20_ABI)

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            logger.warning("⚠️ Gagal baca decimals, pakai default 6 (USDT)")
            decimals = 6

        value = int(amount * (10 ** decimals))

        # log saldo sebelum kirim
        get_usdt_balance(ETH_ACCOUNT.address)
        get_usdt_balance(destination_wallet)

        # ambil nonce pending (untuk menghindari replacement underpriced)
        nonce = w3_eth.eth.get_transaction_count(ETH_ACCOUNT.address, "pending")

        # gas price aman (20% lebih tinggi dari network)
        current_gas_price = w3_eth.eth.gas_price
        safe_gas_price = int(current_gas_price * 1.2)

        tx = contract.functions.transfer(
            Web3.to_checksum_address(destination_wallet),
            value
        ).build_transaction({
            "chainId": ETH_CHAIN_ID,
            "gas": 100000,
            "gasPrice": safe_gas_price,
            "nonce": nonce,
        })

        signed_tx = w3_eth.eth.account.sign_transaction(tx, ETH_ACCOUNT.key)
        tx_hash = w3_eth.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"🕓 Menunggu konfirmasi transaksi {tx_hash.hex()}...")

        # tunggu mined & status sukses
        receipt = w3_eth.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        if receipt.status == 1:
            logger.info(f"✅ USDT ERC20 berhasil masuk ke {destination_wallet}, tx_hash={tx_hash.hex()}")
            # log saldo setelah kirim
            get_usdt_balance(ETH_ACCOUNT.address)
            get_usdt_balance(destination_wallet)
        else:
            logger.error(f"❌ Transaksi gagal masuk blockchain: {tx_hash.hex()}")

        return tx_hash.hex() if receipt.status == 1 else None

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT ERC20: {e}", exc_info=True)
        return None
