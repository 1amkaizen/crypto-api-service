# 📍 main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# ====================== ROUTER CRYPTO ======================
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
from routers.crypto.wallet_monitor import monitor_router

# ====================== MIDDLEWARE ======================
from lib.middleware import api_key
from lib.middleware.api_usage import APIUsageMiddleware
from lib.middleware.api_limit import api_rate_limit_middleware

# ====================== APP ======================
app = FastAPI(
    title="Crypto API Service",
    description="API untuk kirim token crypto (ETH, USDT, BNB, SOL, dll)",
    version="1.0.0",
)

# ====================== REGISTER CRYPTO ROUTERS ======================
crypto_routers = [
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
    monitor_router,
]

for r in crypto_routers:
    app.include_router(r, prefix="/api/v1/crypto", tags=["Crypto"])

# ====================== MIDDLEWARE ======================
app.include_router(api_key.router)
app.add_middleware(APIUsageMiddleware)
app.middleware("http")(api_rate_limit_middleware)


# ====================== CUSTOM OPENAPI (HANYA CRYPTO) ======================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    crypto_routes = [
        route for route in app.routes if "Crypto" in getattr(route, "tags", [])
    ]

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=crypto_routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
