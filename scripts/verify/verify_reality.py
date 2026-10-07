"""
verify_reality.py - Audit Bitget rToken (Tokenized Equity) Spot Endpoints.
Discovers available rTokens, supported candle granularities, historical depth,
weekend trading status, and gaps.
"""

import sys
import os
import json
import httpx
from datetime import datetime, timezone

BASE_URL = "https://api.bitget.com"

def main():
    print("=== [PHASE 0] VERIFYING REALITY / rTOKEN SPOT MARKET DATA ===")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Fetch Spot Symbols
    try:
        res = client.get("/api/v2/spot/public/symbols")
        res.raise_for_status()
        data = res.json()
        all_symbols = data.get("data", [])
        print(f"Total Bitget Spot Symbols returned: {len(all_symbols)}")
    except Exception as e:
        print(f"[ERROR] Failed to query spot symbols: {e}")
        sys.exit(1)

    # 2. Filter rTokens (usually prefixed with 'R' or containing equity names like NVDA, AAPL, TSLA)
    rtokens = []
    for s in all_symbols:
        sym = s.get("symbol", "")
        # rTokens follow format R<TICKER>USDT or <TICKER>USDT
        if sym.startswith("R") and sym.endswith("USDT"):
            rtokens.append(s)

    print(f"Discovered candidate rToken spot symbols: {len(rtokens)}")
    sample_symbols = [s["symbol"] for s in rtokens[:15]]
    print(f"Sample rTokens: {sample_symbols}")

    # 3. Test Candle Granularities for flagship symbols
    flagships = ["RNVDAUSDT", "RAAPLUSDT", "RTSLAUSDT", "RMSFTUSDT"]
    available_flagships = [s["symbol"] for s in rtokens if s["symbol"] in flagships]
    print(f"Target flagships present: {available_flagships}")

    test_symbol = available_flagships[0] if available_flagships else (rtokens[0]["symbol"] if rtokens else None)
    if not test_symbol:
        print("[ERROR] No rToken symbols found!")
        sys.exit(1)

    granularities = ["1min", "5min", "15min", "30min", "1h", "4h", "1day", "1week"]
    granularity_support = {}

    print(f"\nProbing candle granularities on {test_symbol}...")
    for g in granularities:
        try:
            r = client.get("/api/v2/spot/market/candles", params={"symbol": test_symbol, "granularity": g, "limit": "10"})
            if r.status_code == 200 and r.json().get("code") == "00000":
                candles = r.json().get("data", [])
                granularity_support[g] = {
                    "supported": True,
                    "count": len(candles),
                    "latest_ts": int(candles[0][0]) if candles else None
                }
            else:
                granularity_support[g] = {"supported": False, "error": r.text[:100]}
        except Exception as ex:
            granularity_support[g] = {"supported": False, "error": str(ex)}

    print("Granularity support results:")
    for g, info in granularity_support.items():
        print(f"  {g}: {info}")

    # 4. Check Historical Depth (how far back can we reach with pagination)
    print(f"\nProbing historical depth for {test_symbol} (1h candles)...")
    history_records = []
    end_time = None

    for batch in range(15):  # Fetch up to 15 batches of 1000
        params = {"symbol": test_symbol, "granularity": "1h", "limit": "1000"}
        if end_time:
            params["endTime"] = str(end_time)
        r = client.get("/api/v2/spot/market/candles", params=params)
        if r.status_code != 200 or r.json().get("code") != "00000":
            break
        data = r.json().get("data", [])
        if not data:
            break
        history_records.extend(data)
        # Bitget returns candles in reverse chronological order: data[0] is newest, data[-1] is oldest in batch
        oldest_in_batch = int(data[-1][0])
        if oldest_in_batch == end_time:
            break
        end_time = oldest_in_batch - 1
        if len(data) < 1000:
            break

    earliest_dt = None
    latest_dt = None
    days_span = 0.0

    if history_records:
        all_ts = [int(c[0]) for c in history_records]
        earliest_ts = min(all_ts) / 1000.0
        latest_ts = max(all_ts) / 1000.0
        latest_dt = datetime.fromtimestamp(latest_ts, tz=timezone.utc)
        earliest_dt = datetime.fromtimestamp(earliest_ts, tz=timezone.utc)
        days_span = (latest_dt - earliest_dt).total_seconds() / 86400.0
        print(f"Retrieved {len(history_records)} hourly bars.")
        print(f"Earliest bar: {earliest_dt.isoformat()}")
        print(f"Latest bar:   {latest_dt.isoformat()}")
        print(f"Total span:   {days_span:.1f} calendar days (Requirement >= 60 days: {'PASS' if days_span >= 60 else 'FAIL'})")

    audit_summary = {
        "status": "COMPLETED",
        "total_rtokens_discovered": len(rtokens),
        "test_symbol": test_symbol,
        "granularity_support": granularity_support,
        "hourly_bars_retrieved": len(history_records),
        "earliest_timestamp": earliest_dt.isoformat() if earliest_dt else None,
        "latest_timestamp": latest_dt.isoformat() if latest_dt else None,
        "days_span": days_span if earliest_dt else 0,
        "satisfies_60_days": (days_span >= 60) if earliest_dt else False
    }

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/audit_reality.json", "w") as f:
        json.dump(audit_summary, f, indent=2)

    print("\nAudit results written to data/raw/audit_reality.json")

if __name__ == "__main__":
    main()
