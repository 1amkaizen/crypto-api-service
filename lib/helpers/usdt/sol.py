# 📍 lib/helpers/usdt/sol.py
import logging
import os
import base58
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer_checked, create_associated_token_account, get_associated_token_address,TransferCheckedParams
from solders.transaction import Transaction


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
USDT_MINT_ADDRESS = os.getenv("SOL_USDT_ADDRESS")  # USDT SPL token address
SECRET_KEY_BASE58 = os.getenv("SOLANA_PRIVATE_KEY")  # Admin private key

client = Client(SOLANA_RPC_URL)

# Load keypair
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


def get_or_create_ata(owner_pub: Pubkey, mint_pub: Pubkey, payer: Keypair) -> Pubkey:
    """Cek atau buat Associated Token Account (ATA) pakai Transaction.new_signed_with_payer"""
    token_account = get_associated_token_address(owner_pub, mint_pub)
    resp = client.get_account_info(token_account)
    if resp.value is None:
        logger.info(f"⚠️ ATA belum ada, membuat untuk {owner_pub}")
        tx = Transaction.new_signed_with_payer(
            [create_associated_token_account(payer=payer.pubkey(), owner=owner_pub, mint=mint_pub)],
            payer=payer.pubkey(),
            signing_keypairs=[payer],
            recent_blockhash=client.get_latest_blockhash().value.blockhash
        )
        sig = send_tx(tx, payer)
        logger.info(f"✅ ATA dibuat untuk {owner_pub}, sig={sig}")
    return token_account


def get_usdt_balance(wallet_address: str) -> float:
    """Cek saldo USDT SPL di wallet tertentu"""
    try:
        owner_pub = Pubkey.from_string(wallet_address)
        mint_pub = Pubkey.from_string(USDT_MINT_ADDRESS)
        token_account = get_associated_token_address(owner_pub, mint_pub)
        resp = client.get_account_info(token_account)
        if resp.value is None:
            logger.info(f"ℹ️ ATA belum ada untuk {wallet_address}, saldo = 0")
            return 0.0

        bal_resp = client.get_token_account_balance(token_account)
        balance_raw = int(bal_resp.value.amount)
        decimals = int(bal_resp.value.decimals)
        balance = balance_raw / (10 ** decimals)
        logger.info(f"💰 Saldo USDT {wallet_address}: {balance} USDT")
        return balance

    except Exception as e:
        logger.error(f"❌ Gagal cek saldo USDT: {e}", exc_info=True)
        return 0.0


def send_tx(tx: Transaction, signer: Keypair) -> str:
    """Helper untuk kirim transaction, return string signature"""
    raw_txn = bytes(tx)
    resp = client.send_raw_transaction(
        raw_txn,
        opts=TxOpts(skip_preflight=False, preflight_commitment="confirmed")
    )
    signature = getattr(resp, "value", None)
    # Jika Signature object dari solders, ubah ke string base58
    if signature is not None and hasattr(signature, "to_string"):
        return signature.to_string()
    return str(signature)



def send_usdt_solana(destination_wallet: str, amount: float):
    """Kirim USDT SPL ke wallet tujuan"""
    try:
        if not ADMIN_KEYPAIR:
            raise Exception("Private key tidak ditemukan!")

        if destination_wallet == str(ADMIN_KEYPAIR.pubkey()):
            logger.warning(f"❌ Destination sama dengan source! Transaksi dibatalkan: {destination_wallet}")
            return None

        mint_pub = Pubkey.from_string(USDT_MINT_ADDRESS)
        dest_pub = Pubkey.from_string(destination_wallet)
        decimals = 6
        amount_int = int(amount * (10 ** decimals))

        # Pastikan ATA sender & receiver ada
        sender_ata = get_or_create_ata(ADMIN_KEYPAIR.pubkey(), mint_pub, ADMIN_KEYPAIR)
        dest_ata = get_or_create_ata(dest_pub, mint_pub, ADMIN_KEYPAIR)

        # Buat transaksi transfer pakai new_signed_with_payer
        tx_transfer = Transaction.new_signed_with_payer(
            [transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=sender_ata,
                    mint=mint_pub,
                    dest=dest_ata,
                    owner=ADMIN_KEYPAIR.pubkey(),
                    amount=amount_int,
                    decimals=decimals
                )
            )],
            payer=ADMIN_KEYPAIR.pubkey(),
            signing_keypairs=[ADMIN_KEYPAIR],
            recent_blockhash=client.get_latest_blockhash().value.blockhash
        )


        sig = send_tx(tx_transfer, ADMIN_KEYPAIR)
        logger.info(f"✅ USDT SOL berhasil dikirim ke {destination_wallet}, sig={sig}")
        return sig

    except Exception as e:
        logger.error(f"❌ Gagal kirim USDT SOL: {e}", exc_info=True)
        return None
