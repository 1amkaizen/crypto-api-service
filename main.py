# 📍 main.py
from fastapi import FastAPI
from routers.crypto.ping import ping_router
from routers.crypto.send import send_router
from routers.crypto.balance import balance_router
from routers.crypto.price import price_router
from routers.crypto.history import history_router
from routers.crypto.estimate_gas import estimate_gas_router
from routers.crypto.tokens import tokens_router
from routers.crypto.swap import swap_router
from routers.crypto.token_info import token_info_router
from routers.crypto.tx_status import tx_status_router
from routers.crypto.webhook import webhook_router



app = FastAPI(
    title="Crypto API Service",
    description="API untuk kirim token crypto (ETH, USDT, BNB, SOL, dll)",
    version="1.0.0",
)

# ====================== REGISTER ROUTERS ======================
routers = [
    ping_router,
    send_router,
    balance_router,
    price_router,
    history_router,
    estimate_gas_router,
    tokens_router,
    swap_router,
    token_info_router,
    tx_status_router,
    webhook_router,
]

for r in routers:
    app.include_router(r, prefix="/api/v1/crypto", tags=["Crypto"])
