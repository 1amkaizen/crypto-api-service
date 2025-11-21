# 📍 lib/monitor/bsc.py
import os
import asyncio
import logging
from datetime import datetime, timezone
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from lib.supabase_client import supabase
from lib.coingecko import get_current_price

# ================== LOGGING ==================
logger = logging.getLogger("monitor.bsc")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s %(name)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================== KONFIG ==================
BSC_WSS = os.getenv("BSC_WSS_URL")
ADMIN_WALLET = Web3.to_checksum_address(os.getenv("BSC_ADMIN_WALLET"))


class BSCMonitor:
    def __init__(self):
        self.supabase = supabase
        self.wallet_admin = ADMIN_WALLET
        self.tolerance = 0.0001  # toleransi BNB
        self.w3 = Web3(Web3.LegacyWebSocketProvider(BSC_WSS))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        if not self.w3.is_connected():
            logger.error("❌ Gagal connect ke BSC WSS")
        else:
            logger.info("🔗 Connected ke BSC WSS")

    # parsing transfer BNB ke wallet admin
    def parse_transfer(self, tx_hash: str):
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            to_addr = tx['to']
            value_bnb = self.w3.from_wei(tx['value'], 'ether')
            if to_addr and to_addr.lower() == self.wallet_admin.lower() and value_bnb > 0:
                sender = tx['from']
                return float(value_bnb), sender, to_addr
            return None, None, None
        except Exception as e:
            logger.error(f"❌ parse_transfer error: {e}")
            return None, None, None

    async def handle_tx(self, tx_hash: str):
        amount, sender, receiver = self.parse_transfer(tx_hash)
        logger.info(f"🔹 Handle tx {tx_hash} | amount={amount}, sender={sender}, receiver={receiver}")
        if not amount:
            return

        bnb_price_idr = await get_current_price("binancecoin")  # ✅ pakai id coingecko
        logger.info(f"💲 Harga BNB real-time: {bnb_price_idr} IDR")

        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            block = self.w3.eth.get_block(receipt['blockNumber'])
            block_time = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)
        except Exception as e:
            logger.error(f"❌ get_receipt/block gagal: {e}")
            return

        # Loop orders tapi HANYA UPDATE DB, tanpa notif & disburse
        orders = self.supabase.table("TransactionsJual").select("*").eq("status", "waiting_payment").execute().data
        for order in orders:
            order_time = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
            if block_time < order_time:
                continue

            expected_amount = order.get("unique_amount_crypto") or order.get("amount_crypto")
            if expected_amount is None:
                continue

            expected_amount = float(expected_amount)
            wallet_tujuan = order["recipient_wallet"]
            diff = abs(amount - expected_amount)

            if wallet_tujuan.lower() == receiver.lower() and diff <= self.tolerance:
                try:
                    self.supabase.table("TransactionsJual").update(
                        {
                            "status": "paid",
                            "signature": tx_hash,
                            "sender_wallet": sender,
                            "user_notified": False,
                        }
                    ).eq("id", order["id"]).execute()
                    logger.info(f"✅ Order {order['id']} match → status PAID")
                    break
                except Exception:
                    logger.exception(f"❌ Gagal update DB untuk order {order['id']}")

    # ================== WEBSOCKET SUBSCRIBE ==================
    async def subscribe_pending_txs(self):
        last_block = self.w3.eth.block_number
        while True:
            try:
                latest_block = self.w3.eth.get_block('latest', full_transactions=True)
                for tx in latest_block.transactions:
                    to_addr = getattr(tx, 'to', None) or tx.get('to')
                    if to_addr and to_addr.lower() == self.wallet_admin.lower():
                        tx_hash = getattr(tx, 'hash', None) or tx.get('hash')
                        if isinstance(tx_hash, bytes):
                            tx_hash = tx_hash.hex()
                        asyncio.create_task(self.handle_tx(tx_hash))
                last_block = latest_block.number
            except Exception as e:
                logger.error(f"❌ Error di loop block: {e}, retry dalam 5s...")
            await asyncio.sleep(2)  # loop tiap 2 detik


# ================== ENTRY POINT ==================
async def run_monitor(order_id: str):
    monitor = BSCMonitor()
    monitor.order_id = order_id
    await monitor.subscribe_pending_txs()
