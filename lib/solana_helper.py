# 📍 lib/solana_helper.py
import logging
import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.system_program import transfer, TransferParams
from solana.rpc.api import Client
from solana.rpc.types import TxOpts  # ✅ perbaikan

logger = logging.getLogger(__name__)


def create_admin_keypair(private_key: str):
    """Buat Keypair dari private key base58/bytes dari endpoint"""
    if not private_key:
        raise ValueError("❌ Private key harus diberikan!")

    key_bytes = base58.b58decode(private_key)
    if len(key_bytes) == 32:
        return Keypair.from_secret_key(key_bytes)
    elif len(key_bytes) == 64:
        return Keypair.from_bytes(key_bytes)
    else:
        raise ValueError(
            f"❌ Private key salah, panjang {len(key_bytes)} bukan 32/64 bytes"
        )


def send_sol(
    destination_wallet: str, amount_sol: float, rpc_url: str, private_key: str
):
    """Kirim SOL ke wallet tujuan, RPC & private key dikirim dari endpoint"""
    try:
        if not rpc_url:
            raise ValueError("❌ RPC URL harus diberikan!")
        if not private_key:
            raise ValueError("❌ Private key harus diberikan!")

        client = Client(rpc_url)
        admin_keypair = create_admin_keypair(private_key)

        if destination_wallet == str(admin_keypair.pubkey()):
            logger.warning(
                f"❌ Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}"
            )
            return None

        lamports = int(amount_sol * 1_000_000_000)
        logger.info(
            f"🚀 Kirim {amount_sol} SOL ({lamports} lamports) ke {destination_wallet}"
        )

        blockhash_resp = client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash

        tx_instruction = transfer(
            TransferParams(
                from_pubkey=admin_keypair.pubkey(),
                to_pubkey=Pubkey.from_string(destination_wallet),
                lamports=lamports,
            )
        )

        txn = Transaction.new_signed_with_payer(
            [tx_instruction],
            payer=admin_keypair.pubkey(),
            signing_keypairs=[admin_keypair],
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


def get_balance(address: str, rpc_url: str):
    """Cek saldo SOL dari address tertentu, RPC dikirim dari endpoint"""
    try:
        if not rpc_url:
            raise ValueError("❌ RPC URL harus diberikan!")
        if not address:
            raise ValueError("❌ Address harus diberikan!")

        client = Client(rpc_url)
        resp = client.get_balance(Pubkey.from_string(address))
        lamports = (
            getattr(resp.value, "value", None)
            if hasattr(resp.value, "value")
            else getattr(resp, "value", 0)
        )
        sol_balance = lamports / 1_000_000_000
        logger.info(f"💰 Saldo {address}: {sol_balance} SOL")
        return sol_balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo {address}: {e}", exc_info=True)
        return None
