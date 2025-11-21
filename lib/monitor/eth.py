# 📍 lib/monitor/eth.py
import os
import asyncio
import logging
from datetime import datetime, timezone
from web3 import Web3
from lib.supabase_client import supabase
from lib.coingecko import get_current_price

# ================== LOGGING ==================
logger = logging.getLogger("monitor.ethereum")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s %(name)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================== KONFIG ==================
ETH_WSS = os.getenv("ETH_WSS_URL")
ADMIN_WALLET = Web3.to_checksum_address(os.getenv("ETH_ADMIN_WALLET"))


class EthereumMonitor:
    def __init__(self):
        self.supabase = supabase
        self.wallet_admin = ADMIN_WALLET
        self.tolerance = 0.0001  # toleransi ETH
        self.w3 = Web3(Web3.LegacyWebSocketProvider(ETH_WSS))
        self.processed_txs = set()
        if not self.w3.is_connected():
            logger.error("❌ Gagal connect ke Ethereum WSS")
        else:
            logger.info("🔗 Connected ke Ethereum WSS")

    async def get_transaction(self, tx_hash: str):
        try:
            tx = await asyncio.to_thread(self.w3.eth.get_transaction, tx_hash)
            return tx
        except Exception as e:
            logger.error(f"❌ get_transaction error: {e}")
            return None

    async def handle_tx(self, tx_hash: str):
        tx = await self.get_transaction(tx_hash)
        if not tx:
            return

        to_addr = tx["to"]
        value_eth = self.w3.from_wei(tx["value"], "ether")

        if (
            not to_addr
            or to_addr.lower() != self.wallet_admin.lower()
            or value_eth <= 0
        ):
            logger.info(f"ℹ️ Tx {tx_hash} bukan transfer ke {self.wallet_admin}")
            return

        sender = tx["from"]
        eth_price_idr = await get_current_price("eth")
        try:
            receipt = await asyncio.to_thread(
                self.w3.eth.get_transaction_receipt, tx_hash
            )
            block = await asyncio.to_thread(
                self.w3.eth.get_block, receipt["blockNumber"]
            )
            block_time = datetime.fromtimestamp(block["timestamp"], tz=timezone.utc)
        except Exception as e:
            logger.error(f"❌ Gagal ambil block/receipt: {e}")
            block_time = datetime.now(timezone.utc)

        logger.info(
            f"💰 Deposit {value_eth} ETH ({value_eth*eth_price_idr:.2f} IDR) dari {sender} ke {to_addr} (tx={tx_hash})"
        )

        # Simpan ke DB
        try:
            self.supabase.table("transactions").insert(
                {
                    "wallet": to_addr,
                    "sender": sender,
                    "amount": float(value_eth),
                    "signature": tx_hash,
                    "timestamp": block_time.isoformat(),
                }
            )
            logger.info("✅ Transaksi tersimpan di DB")
        except Exception as e:
            logger.error(f"❌ Gagal simpan transaksi: {e}")

    async def subscribe_pending_txs(self):
        while True:
            try:
                latest_block = await asyncio.to_thread(
                    self.w3.eth.get_block, "latest", full_transactions=True
                )
                for tx in latest_block.transactions:
                    to_addr = getattr(tx, "to", None) or tx.get("to")
                    if to_addr and to_addr.lower() == self.wallet_admin.lower():
                        tx_hash = getattr(tx, "hash", None) or tx.get("hash")
                        if isinstance(tx_hash, bytes):
                            tx_hash = tx_hash.hex()
                        if tx_hash not in self.processed_txs:   # <--- cek dulu
                            self.processed_txs.add(tx_hash)
                            asyncio.create_task(self.handle_tx(tx_hash))
            except Exception as e:
                logger.error(f"❌ Error di loop block: {e}, retry 5s")
                await asyncio.sleep(5)
            await asyncio.sleep(2)


# ================== ENTRY POINT ==================
async def run_monitor():
    monitor = EthereumMonitor()
    await monitor.subscribe_pending_txs()
