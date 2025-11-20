# 📍 lib/wallet_validator.py
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_wallet(chain: str, wallet: str) -> tuple[bool, str|None]:
    """
    Validasi wallet address berdasarkan chain.
    Return tuple: (is_valid, normalized_chain_or_none)
    """
    wallet = wallet.strip()
    chain_lower = chain.lower()
    logger.info("Validating wallet '%s' for chain '%s'", wallet, chain_lower)

    # === EVM chains (ETH, BSC, Base, USDT, USDC) ===
    evm_chains = ["eth", "bsc", "bnb", "base", "usdt", "usdc"]
    if chain_lower in evm_chains:
        if not wallet.startswith("0x"):
            wallet = "0x" + wallet
            logger.debug("Auto-prefixed 0x: %s", wallet)
        if re.fullmatch(r"0x[a-fA-F0-9]{40}", wallet):
            logger.info("Valid EVM wallet detected for chain %s", chain_lower)
            # Normalize BNB -> bsc for consistent naming
            normalized_chain = chain_lower
            return True, normalized_chain
        logger.warning("Invalid EVM wallet for chain %s: %s", chain_lower, wallet)
        return False, chain_lower

    # === SOLANA ===
    if chain_lower == "sol":
        if re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", wallet):
            logger.info("Valid SOL wallet detected")
            return True, "sol"
        logger.warning("Invalid SOL wallet: %s", wallet)
        return False, "sol"

    # === TRON ===
    if chain_lower == "trx":
        if re.fullmatch(r"T[a-zA-Z0-9]{33}", wallet):
            logger.info("Valid TRX wallet detected")
            return True, "trx"
        logger.warning("Invalid TRX wallet: %s", wallet)
        return False, "trx"

    # === TON ===
    if chain_lower == "ton":
        if re.fullmatch(r"U[0-9A-Za-z]{47,66}", wallet):
            logger.info("Valid TON wallet detected")
            return True, "ton"
        logger.warning("Invalid TON wallet: %s", wallet)
        return False, "ton"

    # fallback
    logger.error("Unknown chain: %s", chain_lower)
    return False, None
