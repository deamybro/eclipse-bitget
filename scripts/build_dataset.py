"""
scripts/build_dataset.py - Unified CHRONOS Multi-Asset Dataset Builder.
Loads raw market snapshots, applies strict backward as-of alignment,
computes basis and session features, tags data quality, and saves
immutable Parquet tables with SHA-256 checksums in data/manifest.json.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.chronos.sessions import get_market_session, evaluate_session_state
from src.chronos.calendar import US_EQUITY_CALENDAR
from src.chronos.asof import asof_backward_join, verify_zero_lookahead

TZ_UTC = ZoneInfo("UTC")

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_candles_json(filepath: str, symbol: str, is_perp: bool = False) -> pd.DataFrame:
    with open(filepath, "r") as f:
        raw_data = json.load(f)
    
    # Bitget candle format: [timestamp, open, high, low, close, volume, quote_volume]
    records = []
    for row in raw_data:
        records.append({
            "timestamp_utc": pd.to_datetime(int(row[0]), unit="ms", utc=True),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "quote_volume": float(row[6]) if len(row) > 6 else float(row[4]) * float(row[5]),
        })
    
    df = pd.DataFrame(records)
    df = df.sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)
    return df

def parse_funding_json(filepath: str) -> pd.DataFrame:
    with open(filepath, "r") as f:
        raw_data = json.load(f)
    records = []
    for row in raw_data:
        records.append({
            "timestamp_utc": pd.to_datetime(int(row["fundingTime"]), unit="ms", utc=True),
            "funding_rate": float(row["fundingRate"])
        })
    df = pd.DataFrame(records).sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)
    return df

def main():
    print("=== [PHASE 1] BUILDING SYNCHRONIZED CHRONOS DATASET ===")
    os.makedirs("data/normalized", exist_ok=True)
    
    # Target triad pairs: (underlying, rtoken_file, perp_file, funding_file)
    triad_configs = [
        {
            "underlying": "NVDA",
            "rtoken_file": "data/raw/spot_RNVDAUSDT_1h.json",
            "perp_file": "data/raw/perp_NVDAUSDT_1h.json",
            "funding_file": "data/raw/funding_NVDAUSDT.json"
        },
        {
            "underlying": "TSLA",
            "rtoken_file": "data/raw/spot_RTSLAUSDT_1h.json",
            "perp_file": "data/raw/perp_TSLAUSDT_1h.json",
            "funding_file": "data/raw/funding_TSLAUSDT.json"
        },
        {
            "underlying": "AAPL",
            "rtoken_file": "data/raw/spot_RAAPLUSDT_1h.json",
            "perp_file": "data/raw/perp_AAPLUSDT_1h.json",
            "funding_file": "data/raw/funding_AAPLUSDT.json"
        }
    ]

    # Load benchmark crypto series (BTC & ETH) for factor modeling in SHOCKWAVE
    btc_df = parse_candles_json("data/raw/perp_BTCUSDT_1h.json", "BTCUSDT")
    btc_df = btc_df.rename(columns={"close": "btc_close", "volume": "btc_volume"})[["timestamp_utc", "btc_close", "btc_volume"]]
    btc_df["btc_return"] = np.log(btc_df["btc_close"] / btc_df["btc_close"].shift(1)).fillna(0.0)

    eth_df = parse_candles_json("data/raw/perp_ETHUSDT_1h.json", "ETHUSDT")
    eth_df = eth_df.rename(columns={"close": "eth_close", "volume": "eth_volume"})[["timestamp_utc", "eth_close", "eth_volume"]]
    eth_df["eth_return"] = np.log(eth_df["eth_close"] / eth_df["eth_close"].shift(1)).fillna(0.0)

    all_triad_dfs = []

    for cfg in triad_configs:
        underlying = cfg["underlying"]
        print(f"\nProcessing triad representation for {underlying}...")
        
        if not (os.path.exists(cfg["rtoken_file"]) and os.path.exists(cfg["perp_file"])):
            print(f"  Missing files for {underlying}, skipping.")
            continue
            
        rtoken_df = parse_candles_json(cfg["rtoken_file"], f"R{underlying}USDT")
        perp_df = parse_candles_json(cfg["perp_file"], f"{underlying}USDT")
        
        # Rename columns to avoid collisions
        rtoken_df = rtoken_df.rename(columns={
            "open": "rtoken_open", "high": "rtoken_high", "low": "rtoken_low",
            "close": "rtoken_close", "volume": "rtoken_volume", "quote_volume": "rtoken_quote_vol"
        })
        perp_df = perp_df.rename(columns={
            "open": "perp_open", "high": "perp_high", "low": "perp_low",
            "close": "perp_close", "volume": "perp_volume", "quote_volume": "perp_quote_vol"
        })

        # 1. Join rToken and Perp using strict backward as-of logic
        # Both are on 1h bars, but as-of guarantees t_rtoken <= t_timestamp
        aligned = asof_backward_join(
            rtoken_df, perp_df, time_col="timestamp_utc", tolerance_seconds=3600
        )
        
        # 2. Join Funding Rates using strict backward as-of
        if os.path.exists(cfg["funding_file"]):
            funding_df = parse_funding_json(cfg["funding_file"])
            aligned = asof_backward_join(
                aligned, funding_df, time_col="timestamp_utc", suffixes=("", "_funding")
            )
            # Forward-fill latest known funding rate until next settlement
            aligned["funding_rate"] = aligned["funding_rate"].ffill().fillna(0.0)
        else:
            aligned["funding_rate"] = 0.0

        # 3. Join Benchmark crypto factors (BTC, ETH)
        aligned = asof_backward_join(aligned, btc_df, time_col="timestamp_utc")
        aligned = asof_backward_join(aligned, eth_df, time_col="timestamp_utc")

        # 4. CHRONOS Session & Freshness features
        sessions = []
        underlying_open_flags = []
        ref_age_seconds = []
        last_cash_close_ts = aligned["timestamp_utc"].iloc[0]

        for idx, row in aligned.iterrows():
            ts = row["timestamp_utc"].to_pydatetime()
            is_hol = US_EQUITY_CALENDAR.is_holiday(ts)
            is_half = US_EQUITY_CALENDAR.is_half_day(ts)
            s_state = evaluate_session_state(ts, last_cash_close_ts, is_hol, is_half)
            
            sessions.append(s_state.session.value)
            underlying_open_flags.append(s_state.underlying_open)
            ref_age_seconds.append(s_state.reference_age_seconds)
            
            if s_state.underlying_open:
                last_cash_close_ts = ts

        aligned["market_session"] = sessions
        aligned["underlying_open"] = underlying_open_flags
        aligned["reference_age_seconds"] = ref_age_seconds
        aligned["underlying"] = underlying
        aligned["rtoken_symbol"] = f"R{underlying}USDT"
        aligned["perp_symbol"] = f"{underlying}USDT"

        # 5. Core Quantitative Features
        # Log Basis: ln(P_perp / P_rtoken)
        aligned["log_basis"] = np.log(aligned["perp_close"] / aligned["rtoken_close"])
        # Log Returns
        aligned["rtoken_return"] = np.log(aligned["rtoken_close"] / aligned["rtoken_close"].shift(1)).fillna(0.0)
        aligned["perp_return"] = np.log(aligned["perp_close"] / aligned["perp_close"].shift(1)).fillna(0.0)
        
        # Realized Volatility (rolling 24h)
        aligned["rtoken_vol_24h"] = aligned["rtoken_return"].rolling(24, min_periods=4).std() * np.sqrt(24 * 365)
        aligned["rtoken_vol_24h"] = aligned["rtoken_vol_24h"].bfill().fillna(0.30)

        # Drop initial NaN rows
        aligned = aligned.dropna(subset=["rtoken_close", "perp_close"]).reset_index(drop=True)
        print(f"  Constructed {len(aligned)} aligned bars for {underlying}.")
        all_triad_dfs.append(aligned)

    if all_triad_dfs:
        combined_df = pd.concat(all_triad_dfs, ignore_index=True)
        combined_df = combined_df.sort_values(["timestamp_utc", "underlying"]).reset_index(drop=True)
        
        output_parquet = "data/normalized/market_triad.parquet"
        combined_df.to_parquet(output_parquet, index=False)
        checksum = compute_sha256(output_parquet)
        
        # Update manifest
        manifest_path = "data/manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            
        manifest["datasets"]["market_triad_normalized"] = {
            "dataset_id": "market_triad_normalized",
            "source": "chronos_synchronized_pipeline",
            "symbols": [cfg["underlying"] for cfg in triad_configs],
            "frequency": "1h",
            "start": combined_df["timestamp_utc"].min().isoformat(),
            "end": combined_df["timestamp_utc"].max().isoformat(),
            "rows": len(combined_df),
            "checksum": checksum,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "quality": "derived"
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
            
        print(f"\nSuccessfully compiled synchronized dataset: {output_parquet}")
        print(f"Total Rows: {len(combined_df)} | SHA-256: {checksum}")

if __name__ == "__main__":
    main()
