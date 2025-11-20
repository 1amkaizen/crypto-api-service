# 📍 lib/explorer_mapper.py
def get_explorer_url(chain: str, signature: str, devnet: bool = False) -> str:
    chain = chain.lower()
    if chain == "sol":
        if devnet:
            return f"https://explorer.solana.com/tx/{signature}?cluster=devnet"
        return f"https://solscan.io/tx/{signature}"
    elif chain == "eth":
        return f"https://etherscan.io/tx/{signature}"
    elif chain == "bnb":
        return f"https://bscscan.com/tx/{signature}"
    elif chain == "trx":
        return f"https://tronscan.org/#/transaction/{signature}"
    elif chain == "base":
        return f"https://basescan.org/tx/{signature}"
    elif chain == "ton":
        return f"https://tonviewer.com/transaction/{signature}"
    else:
        return f"{signature}"  # fallback: cuma tx hash
