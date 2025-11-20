# 📍 lib/monitor/usdt/trx_usdt.py
import os
import asyncio
import logging
from datetime import datetime, timezone
from tronpy import Tron
from tronpy.exceptions import TransactionNotFound
from tronpy.providers import HTTPProvider
from ecerbot.database import supabase
from ecerbot.notifications.jual import JualNotifier
from ecerbot.lib.flip_disburse import disburse
from ecerbot.lib.coingecko import get_current_price
from tronpy.keys import PrivateKey

# ================== LOGGING ==================
logger = logging.getLogger("monitor.trx_usdt")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s %(name)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================== KONFIG ==================
TRON_NODE = os.getenv("TRON_FULL_NODE")
ADMIN_WALLET = os.getenv("TRON_ADMIN_WALLET")
USDT_CONTRACT = os.getenv("TRC20_USDT_ADDRESS")  # TRC20 USDT contract Base58

notifier = JualNotifier()



class TRXUSDTMonitor:
    def __init__(self):
        self.supabase = supabase
        self.wallet_admin = ADMIN_WALLET
        self.client = Tron(provider=HTTPProvider(TRON_NODE))
        self.token_contract = self.client.get_contract(USDT_CONTRACT)  # Hapus 'abi=TRC20_ABI'
        self.decimals = 10 ** 6  # USDT TRX 6 decimals


    # ================== SEND USDT ==================
    async def send_usdt(self, destination_wallet: str, amount: float):
        try:
            value = int(amount * self.decimals)
            admin_key = PrivateKey(bytes.fromhex(os.getenv("TRON_PRIVATE_KEY")))
            tx = (
                self.token_contract.functions.transfer(destination_wallet, value)
                .with_owner(admin_key)  # pake Key object
                .build()
                .sign()
                .broadcast()
            )
            result = tx.wait()
            logger.info(f"✅ Kirim {amount} USDT ke {destination_wallet} berhasil | txid: {result['txid']}")
            return result
        except Exception as e:
            logger.error(f"❌ Gagal kirim USDT: {e}")
            return None

    # ================== HANDLE TX ==================
    async def handle_tx(self, tx_hash: str, amount: float, sender: str, receiver: str):
        logger.info(f"🔹 Handle TRX tx {tx_hash} | amount={amount}, sender={sender}, receiver={receiver}")
        if not amount:
            return

        usdt_price_idr = await get_current_price("usdt")
        logger.info(f"💲 Harga USDT real-time: {usdt_price_idr} IDR")

        try:
            tx_info = self.client.get_transaction_info(tx_hash)
            block_timestamp = tx_info.get("blockTimeStamp")
            if not block_timestamp:
                logger.warning(f"⚠️ Transaksi {tx_hash} tidak punya blockTimeStamp, skip")
                return
            block_time = datetime.fromtimestamp(block_timestamp / 1000, tz=timezone.utc)
        except TransactionNotFound:
            logger.error(f"❌ Transaksi {tx_hash} tidak ditemukan")
            return
        except Exception as e:
            logger.error(f"❌ get_transaction_info gagal: {e}")
            return

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

            if wallet_tujuan.lower() == receiver.lower() and abs(amount - expected_amount) < 1e-6:
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
                    await notifier.notify_admin(order, tx_hash)
                    await notifier.notify_user_processing_tf(order)
                    # ==== disburse via Midtrans ====
                    await disburse(order)
                    break
                except Exception:
                    logger.exception(f"❌ Gagal update DB untuk order {order['id']}")

    # ================== POLLING TRC20 TRANSFERS ==================
    async def subscribe_pending_txs(self):
        logger.info("📌 Mulai monitor TRX USDT")
        processed_txs = set()
        last_block = self.client.get_latest_block_number()

        from tronpy.keys import to_base58check_address

        TRC20_TRANSFER_SIG = "ddf252ad"

        def decode_trc20_topic(topic_hex: str) -> str | None:
            try:
                topic_bytes = bytes.fromhex(topic_hex)
                addr_bytes = topic_bytes[-20:]
                return to_base58check_address(addr_bytes)
            except Exception as e:
                logger.warning(f"⚠️ Gagal decode topic {topic_hex}: {e}")
                return None

        while True:
            try:
                latest_block = self.client.get_latest_block_number()
                for block_num in range(last_block + 1, latest_block + 1):
                    try:
                        block = self.client.get_block(block_num)
                        txs = block.get("transactions") or []
                    except Exception as e_block:
                        logger.warning(f"⚠️ Skip block {block_num} karena error ambil block: {e_block}")
                        continue

                    for tx in txs:
                        tx_id = tx.get("txID")
                        raw_contracts = tx.get("raw_data", {}).get("contract", [])

                        for contract in raw_contracts:
                            try:
                                if contract.get("type") != "TriggerSmartContract":
                                    continue
                                param = contract.get("parameter", {}).get("value", {})
                                contract_address = param.get("contract_address")
                                if not contract_address:
                                    continue

                                try:
                                    contract_addr_b58 = to_base58check_address(contract_address)
                                except Exception as e_addr:
                                    logger.warning(f"⚠️ Skip contract karena error convert address: {e_addr}")
                                    continue
                                if contract_addr_b58 != USDT_CONTRACT:
                                    continue

                                try:
                                    tx_info = self.client.get_transaction_info(tx_id)
                                    event_logs = tx_info.get("log", [])
                                except Exception as e_txinfo:
                                    logger.warning(f"⚠️ Skip tx {tx_id} karena error get_transaction_info: {e_txinfo}")
                                    continue

                                for log in event_logs:
                                    try:
                                        topics = log.get("topics", [])
                                        if len(topics) != 3:
                                            continue
                                        if not topics[0].startswith(TRC20_TRANSFER_SIG):
                                            continue

                                        sender = decode_trc20_topic(topics[1])
                                        receiver = decode_trc20_topic(topics[2])
                                        if not sender or not receiver:
                                            logger.warning(f"⚠️ Skip log {tx_id} karena sender/receiver invalid")
                                            continue

                                        try:
                                            value = int(log.get("data", "0"), 16) / self.decimals
                                        except Exception as e_value:
                                            logger.warning(f"⚠️ Skip log {tx_id} karena error decode value: {e_value}")
                                            continue

                                        if tx_id in processed_txs:
                                            continue
                                        if receiver.lower() != self.wallet_admin.lower():
                                            continue

                                        logger.info(f"📥 Event Transfer: {value} USDT dari {sender} ke {receiver}")
                                        asyncio.create_task(self.handle_tx(tx_id, value, sender, receiver))
                                        processed_txs.add(tx_id)

                                    except Exception as e_log:
                                        logger.warning(f"⚠️ Skip log {tx_id} karena error unknown: {e_log}")
                                        continue

                            except Exception as e_contract:
                                logger.warning(f"⚠️ Skip contract di tx {tx_id} karena error: {e_contract}")
                                continue

                    last_block = block_num

            except Exception as e:
                logger.error(f"❌ Error di loop TRX utama: {e}, retry dalam 5s...")
                await asyncio.sleep(5)

            await asyncio.sleep(2)

# ================== ENTRY POINT ==================
async def run_usdt_monitor(order_id: str, chain: str = "trx"):
    monitor = TRXUSDTMonitor()
    monitor.order_id = order_id
    await monitor.subscribe_pending_txs()
