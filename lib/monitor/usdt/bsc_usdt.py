# 📍 lib/monitor/usdt/bsc_usdt.py
import os
import asyncio
import logging
from datetime import datetime, timezone
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3._utils.events import get_event_data
from ecerbot.database import supabase
from ecerbot.lib.midtrans_disburse import disburse
from ecerbot.notifications.jual import JualNotifier
from ecerbot.lib.coingecko import get_current_price

# ================== LOGGING ==================
logger = logging.getLogger("monitor.bsc_usdt")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s %(name)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================== KONFIG ==================
BSC_WSS = os.getenv("BSC_WSS_URL")
ADMIN_WALLET = Web3.to_checksum_address(os.getenv("BSC_ADMIN_WALLET"))
USDT_CONTRACT = Web3.to_checksum_address(os.getenv("BSC_USDT_ADDRESS"))

notifier = JualNotifier()


class BSCUSDTMonitor:
    def __init__(self):
        self.supabase = supabase
        self.wallet_admin = ADMIN_WALLET
        self.w3 = Web3(Web3.LegacyWebSocketProvider(BSC_WSS))
        # ✅ Inject POA middleware BSC
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)


        if not self.w3.is_connected():
            logger.error("❌ Gagal connect ke BSC WSS")
        else:
            logger.info("🔗 Connected ke BSC WSS")

        # Kontrak token USDT (ERC20)
        self.usdt_contract = self.w3.eth.contract(
            address=USDT_CONTRACT,
            abi=[
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "name": "from", "type": "address"},
                        {"indexed": True, "name": "to", "type": "address"},
                        {"indexed": False, "name": "value", "type": "uint256"}
                    ],
                    "name": "Transfer",
                    "type": "event"
                }
            ]
        )
        self.decimals = self.usdt_contract.functions.decimals().call()
        self.transfer_event_abi = self.usdt_contract.events.Transfer().abi

    # ================== Handle TX ==================
    async def handle_tx(self, tx_hash: str, amount: float, sender: str, receiver: str):
        logger.info(f"🔹 Handle USDT tx {tx_hash} | amount={amount}, sender={sender}, receiver={receiver}")
        if not amount:
            return

        usdt_price_idr = await get_current_price("usdt")
        logger.info(f"💲 Harga USDT real-time: {usdt_price_idr} IDR")

        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            block = self.w3.eth.get_block(receipt['blockNumber'])
            block_time = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)
        except Exception as e:
            logger.error(f"❌ get_receipt/block gagal: {e}")
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
                    await disburse(order)
                    break
                except Exception:
                    logger.exception(f"❌ Gagal update DB untuk order {order['id']}")

    # ================== WEBSOCKET SUBSCRIBE ==================
    async def subscribe_pending_txs(self):
        last_block = self.w3.eth.block_number
        logger.info(f"📌 Mulai monitor dari block {last_block}")

        from eth_utils import keccak
        transfer_topic = Web3.to_hex(keccak(text="Transfer(address,address,uint256)"))

        while True:
            try:
                latest_block = self.w3.eth.block_number

                fromBlock = last_block
                toBlock = latest_block
                if fromBlock > toBlock:
                    await asyncio.sleep(2)
                    continue

                logs = self.w3.eth.get_logs({
                    "fromBlock": fromBlock,
                    "toBlock": toBlock,
                    "address": self.usdt_contract.address,
                    "topics": [transfer_topic]
                })

                for log in logs:
                    try:
                        evt = get_event_data(self.w3.codec, self.transfer_event_abi, log)
                        sender = evt['args']['from']
                        receiver = evt['args']['to']
                        value = evt['args']['value'] / (10 ** self.decimals)
                        tx_hash = evt['transactionHash'].hex()

                        logger.info(f"📥 Event Transfer: {value} token dari {sender} ke {receiver}")

                        if receiver.lower() == self.wallet_admin.lower():
                            asyncio.create_task(self.handle_tx(tx_hash, value, sender, receiver))
                    except Exception as e:
                        logger.error(f"⚠️ Gagal parse log: {e}")

                last_block = latest_block + 1
            except Exception as e:
                logger.error(f"❌ Error di loop block: {e}, retry dalam 5s...")
                await asyncio.sleep(5)
            await asyncio.sleep(2)


# ================== ENTRY POINT ==================
async def run_usdt_monitor(order_id: str, chain: str = "bsc"):
    monitor = BSCUSDTMonitor()
    monitor.order_id = order_id
    await monitor.subscribe_pending_txs()
