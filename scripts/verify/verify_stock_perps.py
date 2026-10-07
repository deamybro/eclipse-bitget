"""
verify_stock_perps.py - Audit Bitget USDT-Futures Stock Perpetual Contracts.
Verifies contract specifications: multipliers, tick sizes, minimum quantities,
and pricing mechanics for equity perpetuals.
"""

import sys
import os
import json
import httpx

BASE_URL = "https://api.bitget.com"

def main():
    print("=== [PHASE 0] VERIFYING BITGET STOCK PERPETUAL CONTRACTS ===")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    try:
        r = client.get("/api/v2/mix/market/contracts", params={"productType": "USDT-FUTURES"})
        r.raise_for_status()
        data = r.json().get("data", [])
        print(f"Total USDT-FUTURES contracts returned: {len(data)}")
    except Exception as e:
        print(f"[ERROR] Failed to query futures contracts: {e}")
        sys.exit(1)

    # Search for equity tickers
    equity_tickers = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "COIN", "MSTR"]
    matching_contracts = []

    for c in data:
        sym = c.get("symbol", "")
        for eq in equity_tickers:
            if sym == f"{eq}USDT" or sym.startswith(eq):
                matching_contracts.append(c)
                break

    print(f"\nDiscovered {len(matching_contracts)} equity perpetual contracts:")
    for mc in matching_contracts:
        sym = str(mc.get('symbol', ''))
        base = str(mc.get('baseCoin', ''))
        mult = str(mc.get('sizeMultiplier', ''))
        min_sz = str(mc.get('minOrderSize', ''))
        prec = str(mc.get('pricePrecision', ''))
        print(f"  Symbol: {sym:<12} Base: {base:<8} SizeMultiplier: {mult:<6} MinOrderSize: {min_sz:<6} PricePrecision: {prec}")

    # Inspect the exact specification of NVDAUSDT if available
    nvda_perp = next((c for c in matching_contracts if c.get("symbol") == "NVDAUSDT"), None)
    if nvda_perp:
        print(f"\nExact contract specification for NVDAUSDT:")
        for k, v in nvda_perp.items():
            print(f"    {k}: {v}")

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/audit_stock_perps.json", "w") as f:
        json.dump({
            "total_contracts": len(data),
            "equity_contracts_discovered": [c.get("symbol") for c in matching_contracts],
            "details": matching_contracts
        }, f, indent=2)

    print("\nAudit results written to data/raw/audit_stock_perps.json")

if __name__ == "__main__":
    main()
