# 📍 lib/eth_helper.py
import logging
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


def get_balance(address: str, rpc_url: str):
    """Cek saldo ETH dari wallet tertentu"""
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("Ethereum RPC tidak terkoneksi!")
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_eth = w3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Saldo {address}: {balance_eth} ETH")
        return balance_eth
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None


async def send_eth(
    destination_wallet: str,
    amount_eth: float,
    order_id: str = None,
    user_id: int = None,
    username: str = None,
    full_name: str = None,
    rpc_url: str = None,
    private_key: str = None,
):
    """
    Kirim ETH ke wallet tujuan.
    rpc_url & private_key bisa dikirim dari endpoint.
    """
    if not rpc_url:
        raise ValueError("❌ RPC URL harus diberikan!")
    if not private_key:
        raise ValueError("❌ Private key harus diberikan!")

    if not private_key.startswith("0x"):
        private_key = "0x" + private_key
    admin_account = Account.from_key(private_key)

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("Ethereum RPC tidak terkoneksi!")

        sender_address = admin_account.address

        if destination_wallet.lower() == sender_address.lower():
            raise Exception(
                f"Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}"
            )

        sender_balance = get_balance(sender_address, rpc_url)
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

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(
            f"✅ Kirim {amount_eth} ETH ke {destination_wallet}, tx_hash: {tx_hash.hex()}"
        )
        return tx_hash.hex()

    except Exception as e:
        logger.error(f"❌ Gagal kirim ETH: {e}", exc_info=True)
        raise e  # crypto_sender.py yang handle notif
