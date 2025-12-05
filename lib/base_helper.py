# 📍 lib/base_helper.py
import logging
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


def get_balance(address: str, rpc_url: str) -> float:
    """Cek saldo BASE (native) dari wallet tertentu menggunakan RPC dari endpoint"""
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("BASE RPC tidak terkoneksi!")
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_base = w3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Saldo {address}: {balance_base} BASE")
        return float(balance_base)
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None


async def send_base(
    destination_wallet: str,
    amount_base: float,
    rpc_url: str,
    private_key: str,
    order_id: str = None,
    user_id: int = None,
    username: str = None,
    full_name: str = None,
):
    """
    Kirim BASE ke wallet tujuan, menggunakan RPC + private key dari endpoint.
    Lempar exception supaya crypto_sender.py yang handle notif/logging.
    """
    try:
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        admin_account = Account.from_key(private_key)

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("BASE RPC tidak terkoneksi!")

        sender_address = admin_account.address

        if destination_wallet.lower() == sender_address.lower():
            raise Exception(
                f"Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}"
            )

        sender_balance = get_balance(sender_address, rpc_url)
        if sender_balance is None or sender_balance < amount_base:
            raise Exception(f"Saldo tidak cukup! Saldo sekarang {sender_balance} BASE")

        nonce = w3.eth.get_transaction_count(sender_address)
        value = w3.to_wei(amount_base, "ether")

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
            f"✅ Kirim {amount_base} BASE ke {destination_wallet}, tx_hash: {tx_hash.hex()}"
        )
        return tx_hash.hex()

    except Exception as e:
        logger.error(f"❌ Gagal kirim BASE: {e}", exc_info=True)
        raise e
