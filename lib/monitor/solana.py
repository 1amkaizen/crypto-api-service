# 📍 lib/monitor/solana.py
import os
import json
import asyncio
import logging
import websockets
import httpx
from datetime import datetime, timezone
from lib.supabase_client import supabase
from lib.coingecko import get_current_price  # ✅ import CoinGecko

# ================== LOGGING ==================
logger = logging.getLogger("monitor.solana")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s %(name)s]: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================== KONFIG ==================
SOLANA_RPC = os.getenv("SOLANA_RPC_URL")
SOLANA_WSS = os.getenv("SOLANA_RPC_WSS")
ADMIN_WALLET = os.getenv("SOLANA_ADMIN_WALLET")


class SolanaMonitor:
    def __init__(self):
        self.supabase = supabase
        self.wallet_admin = ADMIN_WALLET
        self.tolerance = 0.0001  # toleransi jumlah SOL

    # ambil detail transaksi dari signature
    async def get_transaction(self, signature: str):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                signature,
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed",
                    "maxSupportedTransactionVersion": 0,
                },
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(SOLANA_RPC, json=payload)
                r.raise_for_status()
                return r.json().get("result")
        except Exception as e:
            logger.error(f"❌ getTransaction gagal: {e}")
            return None

    # parsing transfer SOL ke wallet admin
    def parse_transfer(self, detail):
        try:
            account_keys = detail["transaction"]["message"]["accountKeys"]
            pre_balances = detail["meta"]["preBalances"]
            post_balances = detail["meta"]["postBalances"]

            for idx, acc in enumerate(account_keys):
                pubkey = acc["pubkey"] if isinstance(acc, dict) else acc
                if pubkey == self.wallet_admin:
                    diff = post_balances[idx] - pre_balances[idx]
                    if diff > 0:
                        amount_sol = diff / 1e9
                        sender = account_keys[0]["pubkey"] if isinstance(account_keys[0], dict) else account_keys[0]
                        return amount_sol, sender, pubkey
            return None, None, None
        except Exception as e:
            logger.error(f"❌ parse_transfer error: {e}")
            return None, None, None

    # handle transaksi yang masuk
    async def handle_tx(self, signature: str):
        detail = await self.get_transaction(signature)
        if not detail:
            return

        amount, sender, receiver = self.parse_transfer(detail)
        if not amount:
            logger.info(f"ℹ️ Tx {signature} bukan transfer ke {self.wallet_admin}")
            return

        # Ambil harga SOL real-time
        sol_price_idr = await get_current_price("sol")
        logger.info(f"💲 Harga SOL real-time: {sol_price_idr} IDR")

        block_time = datetime.fromtimestamp(detail.get("blockTime", datetime.now().timestamp()), tz=timezone.utc)
        logger.info(f"💰 Deposit {amount} SOL ({amount * sol_price_idr:.2f} IDR) dari {sender} ke {receiver} (tx={signature})")

        # Simpan ke DB supabase
        try:
            self.supabase.table("transactions").insert({
                "wallet": receiver,
                "sender": sender,
                "amount": amount,
                "signature": signature,
                "timestamp": block_time.isoformat()
            })
            logger.info(f"✅ Transaksi tersimpan di DB")
        except Exception as e:
            logger.error(f"❌ Gagal simpan transaksi: {e}")

    # subscribe websocket
    async def subscribe_account(self):
        while True:
            try:
                async with websockets.connect(SOLANA_WSS) as ws:
                    sub_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "logsSubscribe",
                        "params": [{"mentions": [self.wallet_admin]}, {"commitment": "confirmed"}],
                    }
                    await ws.send(json.dumps(sub_request))
                    logger.info(f"🔗 Subscribed ke wallet logs {self.wallet_admin}")

                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        if "params" in data and "result" in data["params"]:
                            value = data["params"]["result"].get("value", {})
                            signature = value.get("signature")
                            if signature:
                                logger.info(f"📩 Log baru, signature={signature}")
                                await self.handle_tx(signature)
                        else:
                            logger.debug(f"ℹ️ Non-log message: {json.dumps(data)}")

            except Exception as e:
                logger.error(f"❌ Error di subscription loop: {e}, retry dalam 5s...")
                await asyncio.sleep(5)


# ================== ENTRY POINT ==================
async def run_monitor():
    monitor = SolanaMonitor()
    await monitor.subscribe_account()
