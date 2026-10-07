"""
ingest_market_data.py - Fetch and archive immutable raw historical market data.
Pulls spot rTokens, equity perps, benchmark crypto (BTC, ETH), and funding records.
Calculates SHA-256 checksums and updates data/manifest.json.
"""

import sys
import os
import json
import hashlib
import httpx
from datetime import datetime, timezone
import pandas as pd

BASE_URL = "https://api.bitget.com"

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def fetch_candles_paginated(client: httpx.Client, endpoint: str, params: dict, max_batches: int = 15) -> list:
    all_candles = []
    current_end_time = None

    for _ in range(max_batches):
        p = params.copy()
        if current_end_time:
            p["endTime"] = str(current_end_time)
        
        try:
            r = client.get(endpoint, params=p)
            if r.status_code != 200 or r.json().get("code") != "00000":
                break
            data = r.json().get("data", [])
            if not data:
                break
            all_candles.extend(data)
            # data[-1][0] is oldest in batch
            oldest_ts = int(data[-1][0])
            if oldest_ts == current_end_time:
                break
            current_end_time = oldest_ts - 1
            if len(data) < int(params.get("limit", 1000)):
                break
        except Exception as e:
            print(f"Error fetching candles: {e}")
            break

    # Deduplicate by timestamp
    seen = set()
    deduped = []
    for c in all_candles:
        ts = int(c[0])
        if ts not in seen:
            seen.add(ts)
            deduped.append(c)
    # Sort chronologically ascending
    deduped.sort(key=lambda x: int(x[0]))
    return deduped

def main():
    print("=== [PHASE 1] IMMUTABLE DATA INGESTION ENGINE ===")
    client = httpx.Client(base_url=BASE_URL, timeout=25.0)
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/normalized", exist_ok=True)

    manifest_path = "data/manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    else:
        manifest = {"manifest_version": "1.0.0", "datasets": {}}

    # Target core symbols
    rtoken_symbols = ["RNVDAUSDT", "RAAPLUSDT", "RTSLAUSDT", "RMSFTUSDT"]
    perp_symbols = ["NVDAUSDT", "TSLAUSDT", "AAPLUSDT", "BTCUSDT", "ETHUSDT"]

    ingestion_summary = {}

    # 1. Ingest Spot rToken Candles (1h)
    print("\n[1/3] Ingesting Spot rToken Hourly Candles...")
    for sym in rtoken_symbols:
        print(f"  Fetching {sym} (1h)...")
        candles = fetch_candles_paginated(
            client,
            "/api/v2/spot/market/candles",
            {"symbol": sym, "granularity": "1h", "limit": "1000"}
        )
        if candles:
            raw_file = f"data/raw/spot_{sym}_1h.json"
            with open(raw_file, "w") as f:
                json.dump(candles, f)
            checksum = compute_sha256(raw_file)
            start_iso = datetime.fromtimestamp(int(candles[0][0]) / 1000, tz=timezone.utc).isoformat()
            end_iso = datetime.fromtimestamp(int(candles[-1][0]) / 1000, tz=timezone.utc).isoformat()
            
            dataset_id = f"spot_{sym}_1h"
            manifest["datasets"][dataset_id] = {
                "dataset_id": dataset_id,
                "source": "bitget_spot_v2",
                "symbol": sym,
                "frequency": "1h",
                "start": start_iso,
                "end": end_iso,
                "rows": len(candles),
                "checksum": checksum,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "quality": "observed"
            }
            print(f"    Saved {len(candles)} bars ({start_iso} to {end_iso}) | SHA-256: {checksum[:12]}...")

    # 2. Ingest Mix Futures Perpetual Candles (1h)
    print("\n[2/3] Ingesting Perpetual Futures Hourly Candles...")
    for sym in perp_symbols:
        print(f"  Fetching {sym} (1h)...")
        candles = fetch_candles_paginated(
            client,
            "/api/v2/mix/market/candles",
            {"symbol": sym, "granularity": "1H", "productType": "USDT-FUTURES", "limit": "1000"}
        )
        if candles:
            raw_file = f"data/raw/perp_{sym}_1h.json"
            with open(raw_file, "w") as f:
                json.dump(candles, f)
            checksum = compute_sha256(raw_file)
            start_iso = datetime.fromtimestamp(int(candles[0][0]) / 1000, tz=timezone.utc).isoformat()
            end_iso = datetime.fromtimestamp(int(candles[-1][0]) / 1000, tz=timezone.utc).isoformat()
            
            dataset_id = f"perp_{sym}_1h"
            manifest["datasets"][dataset_id] = {
                "dataset_id": dataset_id,
                "source": "bitget_mix_v2",
                "symbol": sym,
                "frequency": "1h",
                "start": start_iso,
                "end": end_iso,
                "rows": len(candles),
                "checksum": checksum,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "quality": "observed"
            }
            print(f"    Saved {len(candles)} bars ({start_iso} to {end_iso}) | SHA-256: {checksum[:12]}...")

    # 3. Ingest Funding Rate Histories
    print("\n[3/3] Ingesting Historical Funding Rates...")
    for sym in ["NVDAUSDT", "TSLAUSDT", "AAPLUSDT", "BTCUSDT", "ETHUSDT"]:
        print(f"  Fetching funding for {sym}...")
        funding_records = []
        for p in range(1, 10):
            try:
                r = client.get("/api/v2/mix/market/history-fund-rate", params={
                    "symbol": sym, "productType": "USDT-FUTURES", "pageSize": "100", "pageNo": str(p)
                })
                if r.status_code == 200 and r.json().get("code") == "00000":
                    data = r.json().get("data", [])
                    if not data:
                        break
                    funding_records.extend(data)
                else:
                    break
            except Exception:
                break
        
        if funding_records:
            # Deduplicate by fundingTime
            seen = set()
            deduped = []
            for f in funding_records:
                ft = int(f["fundingTime"])
                if ft not in seen:
                    seen.add(ft)
                    deduped.append(f)
            deduped.sort(key=lambda x: int(x["fundingTime"]))

            raw_file = f"data/raw/funding_{sym}.json"
            with open(raw_file, "w") as f:
                json.dump(deduped, f)
            checksum = compute_sha256(raw_file)
            start_iso = datetime.fromtimestamp(int(deduped[0]["fundingTime"]) / 1000, tz=timezone.utc).isoformat()
            end_iso = datetime.fromtimestamp(int(deduped[-1]["fundingTime"]) / 1000, tz=timezone.utc).isoformat()

            dataset_id = f"funding_{sym}"
            manifest["datasets"][dataset_id] = {
                "dataset_id": dataset_id,
                "source": "bitget_mix_funding",
                "symbol": sym,
                "frequency": "8h",
                "start": start_iso,
                "end": end_iso,
                "rows": len(deduped),
                "checksum": checksum,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "quality": "observed"
            }
            print(f"    Saved {len(deduped)} funding settlements ({start_iso} to {end_iso}) | SHA-256: {checksum[:12]}...")

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest successfully updated with {len(manifest['datasets'])} datasets.")

if __name__ == "__main__":
    main()
