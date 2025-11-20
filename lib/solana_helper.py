# 📍 lib/solana_helper.py
import logging
import os
import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solana.rpc.api import Client
from solana.rpc.types import TxOpts  # ✅ perbaikan
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
client = Client(SOLANA_RPC_URL)

# Ambil private key dari .env (base58)
SECRET_KEY_BASE58 = os.getenv("SOLANA_PRIVATE_KEY")
if SECRET_KEY_BASE58:
    key_bytes = base58.b58decode(SECRET_KEY_BASE58)
    if len(key_bytes) == 32:
        ADMIN_KEYPAIR = Keypair.from_secret_key(key_bytes)
    elif len(key_bytes) == 64:
        ADMIN_KEYPAIR = Keypair.from_bytes(key_bytes)
    else:
        raise ValueError(f"❌ Private key salah, panjang {len(key_bytes)} bukan 32/64 bytes")
else:
    ADMIN_KEYPAIR = None


def send_sol(destination_wallet: str, amount_sol: float):
    """Kirim SOL ke wallet tujuan"""
    try:
        if not ADMIN_KEYPAIR:
            raise Exception("Private key tidak ditemukan!")

        if destination_wallet == str(ADMIN_KEYPAIR.pubkey()):
            logger.warning(f"❌ Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}")
            return None

        lamports = int(amount_sol * 1_000_000_000)
        logger.info(f"🚀 Kirim {amount_sol} SOL ({lamports} lamports) ke {destination_wallet}")

        blockhash_resp = client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash

        tx_instruction = transfer(
            TransferParams(
                from_pubkey=ADMIN_KEYPAIR.pubkey(),
                to_pubkey=Pubkey.from_string(destination_wallet),
                lamports=lamports,
            )
        )

        txn = Transaction.new_signed_with_payer(
            [tx_instruction],
            payer=ADMIN_KEYPAIR.pubkey(),
            signing_keypairs=[ADMIN_KEYPAIR],
            recent_blockhash=recent_blockhash,
        )

        raw_txn = bytes(txn)
        resp = client.send_raw_transaction(
            raw_txn,
            opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed"),
        )

        signature = getattr(resp, "value", None)
        logger.info(f"✅ Transaksi berhasil! Signature: {signature}")
        return signature

    except Exception as e:
        logger.error(f"❌ Gagal kirim SOL: {e}", exc_info=True)
        return None


def get_balance(address: str = None):
    """Cek saldo SOL, default ke admin jika address None"""
    try:
        target_address = address or (str(ADMIN_KEYPAIR.pubkey()) if ADMIN_KEYPAIR else None)
        if not target_address:
            raise Exception("❌ Address tidak tersedia!")

        resp = client.get_balance(Pubkey.from_string(target_address))
        lamports = getattr(resp.value, "value", None) if hasattr(resp.value, "value") else getattr(resp, "value", 0)
        sol_balance = lamports / 1_000_000_000
        logger.info(f"💰 Saldo {target_address}: {sol_balance} SOL")
        return sol_balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None
