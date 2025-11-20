# 📍 lib/monitor/usdt/sol_usdt.py (update WS langsung ke admin wallet)
import os
import asyncio
import logging
from decimal import Decimal
import websockets
import json

from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.async_client import AsyncToken
from spl.token.instructions import decode_transfer_checked
from spl.token._layouts import MINT_LAYOUT
from spl.token.instructions import get_associated_token_address

from ecerbot.database import supabase
from ecerbot.notifications.jual import JualNotifier
from ecerbot.lib.flip_disburse import disburse
from ecerbot.lib.coingecko import get_current_price

# ================== LOGGING ==================
logger = logging.getLogger("monitor.sol_usdt")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s %(name)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================== KONFIG ==================
SOLANA_NODE = os.getenv("SOLANA_RPC_WSS")
ADMIN_WALLET = os.getenv("SOLANA_ADMIN_WALLET")
ADMIN_KEYPAIR = os.getenv("SOLANA_PRIVATE_KEY")
USDT_MINT = os.getenv("SOL_USDT_ADDRESS")
DECIMALS = 10**6  # USDT 6 decimals

notifier = JualNotifier()


class SolUSDTMonitor:
    def __init__(self):
        self.supabase = supabase
        self.wallet_admin = ADMIN_WALLET
        self.decimals = DECIMALS
        self.client = AsyncClient(SOLANA_NODE)
        self.keypair = Keypair.from_base58_string(ADMIN_KEYPAIR)

    async def send_usdt(self, destination_wallet: str, amount: float):
        try:
            token = AsyncToken(
                self.client,
                Pubkey.from_string(USDT_MINT),
                TOKEN_PROGRAM_ID,
                self.keypair,
            )
            dest_pubkey = Pubkey.from_string(destination_wallet)
            amount_int = int(amount * self.decimals)

            tx_sig = await token.transfer_checked(
                dest_pubkey,
                self.keypair.pubkey(),
                amount_int,
                6,
                self.keypair,
            )
            logger.info(f"✅ Kirim {amount} USDT ke {destination_wallet} berhasil | txid: {tx_sig}")
            return tx_sig
        except Exception as e:
            logger.error(f"❌ Gagal kirim USDT: {e}")
            return None

    async def handle_tx(self, tx_sig: str, amount: float, sender: str, receiver: str):
        # ✅ pastikan signature dalam bentuk string agar bisa di-JSON-kan
        tx_sig = str(tx_sig)

        logger.info(f"🔹 Handle Solana tx {tx_sig} | amount={amount}, sender={sender}, receiver={receiver}")
        if not amount:
            return

        usdt_price_idr = await get_current_price("usdt")
        logger.info(f"💲 Harga USDT real-time: {usdt_price_idr} IDR")

        # 🔹 Ambil semua order yang menunggu
        orders = (
            self.supabase.table("TransactionsJual")
            .select("*")
            .eq("status", "waiting_payment")
            .execute()
            .data
        )

        for order in orders:
            expected_amount = float(order.get("unique_amount_crypto") or order.get("amount_crypto") or 0)

            if abs(amount - expected_amount) < 1e-6:
                try:
                    self.supabase.table("TransactionsJual").update(
                        {
                            "status": "paid",
                            "signature": tx_sig,   # ✅ sudah string, aman disimpan
                            "sender_wallet": sender,
                            "user_notified": False,
                        }
                    ).eq("id", order["id"]).execute()

                    logger.info(f"✅ Order {order['id']} cocok → status PAID")
                    await notifier.notify_admin(order, tx_sig)
                    await notifier.notify_user_processing_tf(order)

                    logger.info(f"🚀 Jalankan Flip disbursement untuk order {order['id']}")
                    await disburse(order)
                    logger.info(f"✅ Flip disbursement sukses untuk order {order['id']}")
                    break

                except Exception:
                    logger.exception(f"❌ Gagal update DB / Flip disburse order {order['id']}")
 
    
    async def subscribe_pending_txs(self):
        logger.info(f"📌 Mulai monitor Solana USDT (SPL) di wallet admin {self.wallet_admin}")
        processed_sigs: set[str] = set()
        backoff = 1

        # ✅ FIX: Gunakan metode deterministic ATA (tidak bergantung versi solana-py)
        try:
            mint_pubkey = Pubkey.from_string(USDT_MINT)
            owner_pubkey = self.keypair.pubkey()
            ata_pubkey = get_associated_token_address(owner_pubkey, mint_pubkey)
            admin_token_account = str(ata_pubkey)
            logger.info(f"🎯 ATA USDT Admin ditemukan: {admin_token_account}")
        except Exception as e:
            logger.critical(f"❌ Gagal hitung ATA USDT admin: {e}")
            return

        while True:
            try:
                async with websockets.connect(SOLANA_NODE) as ws:
                    await ws.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "accountSubscribe",
                        "params": [
                            admin_token_account,
                            {"encoding": "jsonParsed", "commitment": "confirmed"},
                        ],
                    }))
                    logger.info(f"🔌 WS connected → listening for incoming USDT transfers ke {admin_token_account}")
                    backoff = 1

                    while True:
                        try:
                            raw_msg = await ws.recv()
                            msg = json.loads(raw_msg)
                            logger.debug(f"📥 WS raw message: {repr(msg)}")

                            if "params" in msg and "result" in msg["params"]:
                                account_data = msg["params"]["result"].get("value")
                                if not account_data or "data" not in account_data:
                                    continue

                                parsed = account_data["data"].get("parsed")
                                if not parsed:
                                    continue

                                info = parsed.get("info", {})
                                ui_amount = float(info.get("tokenAmount", {}).get("uiAmount", 0))
                                owner = info.get("owner")

                                sigs = await self.client.get_signatures_for_address(
                                    Pubkey.from_string(admin_token_account),
                                    limit=1
                                )
                                if sigs.value:
                                    sig = sigs.value[0].signature
                                    if sig not in processed_sigs:
                                        processed_sigs.add(sig)
                                        logger.info(f"🔹 Detected incoming USDT transfer, tx: {sig}")
                                        tx = await self.client.get_transaction(sig, encoding="jsonParsed", commitment="confirmed")
                                        if tx.value:
                                            try:
                                                # 🔧 Konversi hasil Solders ke JSON agar bisa dibaca sebagai dict
                                                tx_json = json.loads(tx.value.to_json())  # ✅ ubah string JSON → dict
                                                message = tx_json.get("transaction", {}).get("message", {})

                                                instructions = message.get("instructions", [])

                                                for ix in instructions:
                                                    # filter instruksi transfer SPL Token (transferChecked)
                                                    parsed = ix.get("parsed", {})
                                                    if parsed.get("type") != "transferChecked":
                                                        continue

                                                    info = parsed.get("info", {})
                                                    dest = info.get("destination")
                                                    sender = info.get("source")
                                                    amount = float(info.get("tokenAmount", {}).get("uiAmount", 0))

                                                    if dest and dest.lower() == admin_token_account.lower():
                                                        logger.info(f"✅ Transfer {amount} USDT dari {sender} → {dest}")
                                                        await self.handle_tx(sig, amount, sender, dest)

                                            except Exception as e:
                                                logger.warning(f"⚠️ Gagal parse tx {sig}: {e}")
                                                continue  # ← FIX indent di sini bro

                        except Exception as e:
                            logger.warning(f"⚠️ WS loop error, skip 5s | {repr(e)}")
                            await asyncio.sleep(5)

            except Exception as e:
                logger.critical(f"❌ WS connection gagal, reconnect {backoff}s | {repr(e)}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)


# ================== ENTRY POINT ==================
async def run_usdt_monitor(order_id: str, chain: str = "sol"):
    monitor = SolUSDTMonitor()
    monitor.order_id = order_id
    await monitor.subscribe_pending_txs()
