# 📍 routers/crypto/balance.py
import logging
from fastapi import APIRouter, HTTPException, Query
from lib.balance_checker import check_balance

balance_router = APIRouter()
logger = logging.getLogger(__name__)


@balance_router.get("/balance")
async def get_wallet_balance(
    chain: str = Query(..., description="eth, bsc, bnb, sol, trx"),
    wallet: str = Query(..., description="Alamat wallet"),
    rpc_url: str = Query(..., description="RPC URL mainnet/testnet"),
):
    """
    Cek saldo wallet per chain.
    User harus input RPC URL sendiri (bisa mainnet atau testnet)
    """
    try:
        bal = await check_balance(chain, wallet, rpc_url)
        return {
            "status": "success",
            "chain": chain.upper(),
            "wallet": wallet,
            "balance": bal,
        }
    except Exception as e:
        logger.error(f"❌ Gagal cek saldo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
