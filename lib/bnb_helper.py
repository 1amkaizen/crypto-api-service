# 📍 lib/bnb_helper.py
import logging
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


def get_balance(address: str, rpc_url: str) -> float:
    """Cek saldo BNB dari wallet tertentu, user input RPC URL"""
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("BSC RPC tidak terkoneksi!")
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        balance_bnb = w3.from_wei(balance_wei, "ether")
        logger.info(f"💰 Saldo {address}: {balance_bnb} BNB")
        return float(balance_bnb)
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None


async def send_bnb(
    destination_wallet: str,
    amount_bnb: float,
    rpc_url: str,
    private_key: str,
    order_id=None,
    user_id=None,
    username=None,
):
    """Kirim BNB ke wallet tujuan, user input RPC + private key"""
    try:
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        admin_account = Account.from_key(private_key)

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise Exception("BSC RPC tidak terkoneksi!")

        sender_address = admin_account.address

        if destination_wallet.lower() == sender_address.lower():
            raise Exception("Destination sama dengan source! Transaksi dibatalkan")

        sender_balance = get_balance(sender_address, rpc_url)
        if sender_balance is None or sender_balance < amount_bnb:
            raise Exception(f"Saldo tidak cukup! Saldo sekarang {sender_balance} BNB")

        nonce = w3.eth.get_transaction_count(sender_address)
        value = w3.to_wei(amount_bnb, "ether")

        # Chain ID default: 56 mainnet
        chain_id = 56
        if "testnet" in rpc_url.lower():
            chain_id = 97  # BSC testnet

        tx = {
            "nonce": nonce,
            "to": Web3.to_checksum_address(destination_wallet),
            "value": value,
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "chainId": chain_id,
        }

        logger.info(
            f"🚀 Kirim BNB ke {destination_wallet} | amount={amount_bnb} | "
            f"order_id={order_id} | user_id={user_id} | username={username}"
        )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        # Explorer link
        explorer_base = (
            "https://bscscan.com" if chain_id == 56 else "https://testnet.bscscan.com"
        )
        tx_link = f"{explorer_base}/tx/{tx_hash_hex}"

        logger.info(f"✅ BNB berhasil dikirim! tx_hash: {tx_hash_hex}")
        logger.info(f"🔗 Lihat transaksi di BscScan: {tx_link}")

        return tx_hash_hex

    except Exception as e:
        logger.error(f"❌ Gagal kirim BNB: {e}", exc_info=True)
        return None
