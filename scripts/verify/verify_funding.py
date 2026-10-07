"""
verify_funding.py - Audit Bitget Historical Funding Rates.
Paginates funding rates for equity perps (e.g. NVDAUSDT, TSLAUSDT) to determine
history reach, settlement cadence (8h), and rate distribution.
"""

import sys
import os
import json
import httpx
from datetime import datetime, timezone

BASE_URL = "https://api.bitget.com"

def main():
    print("=== [PHASE 0] VERIFYING BITGET FUNDING RATE HISTORY ===")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    symbols = ["NVDAUSDT", "TSLAUSDT", "BTCUSDT"]
    funding_audit = {}

    for sym in symbols:
        print(f"\nProbing funding history for {sym}...")
        funding_records = []
        page_size = 100
        page_no = 1
        
        try:
            r = client.get("/api/v2/mix/market/history-fund-rate", params={
                "symbol": sym,
                "productType": "USDT-FUTURES",
                "pageSize": str(page_size),
                "pageNo": str(page_no)
            })
            if r.status_code == 200 and r.json().get("code") == "00000":
                records = r.json().get("data", [])
                funding_records.extend(records)
                print(f"  Page 1 returned {len(records)} records.")
                
                # Probe multiple pages to gauge depth
                for p in range(2, 6):
                    r_next = client.get("/api/v2/mix/market/history-fund-rate", params={
                        "symbol": sym,
                        "productType": "USDT-FUTURES",
                        "pageSize": str(page_size),
                        "pageNo": str(p)
                    })
                    if r_next.status_code == 200 and r_next.json().get("code") == "00000":
                        rec_next = r_next.json().get("data", [])
                        if not rec_next:
                            break
                        funding_records.extend(rec_next)
                    else:
                        break

                if funding_records:
                    ts_list = [int(x["fundingTime"]) for x in funding_records if "fundingTime" in x]
                    earliest_ts = min(ts_list) / 1000.0
                    latest_ts = max(ts_list) / 1000.0
                    earliest_dt = datetime.fromtimestamp(earliest_ts, tz=timezone.utc)
                    latest_dt = datetime.fromtimestamp(latest_ts, tz=timezone.utc)
                    days_span = (latest_dt - earliest_dt).total_seconds() / 86400.0
                    
                    rates = [float(x["fundingRate"]) for x in funding_records if "fundingRate" in x]
                    avg_rate = sum(rates) / len(rates) if rates else 0.0
                    
                    print(f"  Total records fetched: {len(funding_records)}")
                    print(f"  Earliest settlement:   {earliest_dt.isoformat()}")
                    print(f"  Latest settlement:     {latest_dt.isoformat()}")
                    print(f"  Coverage span:         {days_span:.1f} days")
                    print(f"  Mean funding rate:     {avg_rate:.6f} ({avg_rate * 3 * 365 * 100:.2f}% annualized)")
                    
                    funding_audit[sym] = {
                        "records_count": len(funding_records),
                        "earliest": earliest_dt.isoformat(),
                        "latest": latest_dt.isoformat(),
                        "days_span": days_span,
                        "mean_rate": avg_rate,
                        "sample_latest": funding_records[:3]
                    }
            else:
                print(f"  [WARN] Failed to fetch funding for {sym}: {r.text[:100]}")
                funding_audit[sym] = {"error": r.text[:100]}
        except Exception as e:
            print(f"  [ERROR] Exception querying funding for {sym}: {e}")
            funding_audit[sym] = {"error": str(e)}

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/audit_funding.json", "w") as f:
        json.dump(funding_audit, f, indent=2)

    print("\nAudit results written to data/raw/audit_funding.json")

if __name__ == "__main__":
    main()
