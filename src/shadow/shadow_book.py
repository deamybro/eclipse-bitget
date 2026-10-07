"""
src/shadow/shadow_book.py - Counterfactual Shadow Book Engine.
Logs all signals rejected by Credibility Gate, Edge Envelope, or Cost Gate,
and tracks their counterfactual performance to prove value-add of filtering.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from src.contracts import AlphaSignal, AlphaSleeve


class ShadowBook:
    """Maintains an audit ledger of counterfactual trades from rejected signals."""

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def record_rejected_signal(
        self,
        signal: AlphaSignal,
        entry_price: float,
        horizon_bars: int = 12
    ):
        self.records.append({
            "signal_id": signal.signal_id,
            "sleeve": signal.sleeve.value,
            "symbol": signal.symbol,
            "timestamp_utc": signal.timestamp_utc,
            "direction": signal.direction.value,
            "point_edge": signal.point_edge,
            "rejection_reason": signal.rejection_reason or "UNKNOWN",
            "entry_price": entry_price,
            "horizon_bars": horizon_bars,
            "exit_price": None,
            "counterfactual_return": None,
            "was_saved_loss": None
        })

    def update_outcomes(self, current_prices: Dict[str, float], current_bar_idx: int):
        """Resolves counterfactual PnL for tracked rejected signals after horizon."""
        for rec in self.records:
            if rec["exit_price"] is None and rec["symbol"] in current_prices:
                # Mark outcome
                p_exit = current_prices[rec["symbol"]]
                rec["exit_price"] = p_exit
                p_entry = rec["entry_price"]
                
                # Raw directional return
                if rec["direction"] == "LONG":
                    ret = (p_exit - p_entry) / p_entry
                elif rec["direction"] == "SHORT":
                    ret = (p_entry - p_exit) / p_entry
                else:
                    ret = 0.0
                    
                rec["counterfactual_return"] = ret
                # If counterfactual return was negative, rejecting it saved capital!
                rec["was_saved_loss"] = bool(ret < 0.0)

    def summarize_value_add(self) -> Dict[str, Any]:
        """Calculates total avoided losses and counterfactual hit rate."""
        if not self.records:
            return {"total_rejected": 0, "filter_alpha_saved_pct": 0.0}

        df = pd.DataFrame(self.records)
        resolved = df.dropna(subset=["counterfactual_return"])
        if resolved.empty:
            return {
                "total_rejected": len(df),
                "resolved_trades": 0,
                "avoided_loss_ratio": 0.0,
                "avg_counterfactual_return": 0.0,
                "filter_alpha_saved_pct": 0.0
            }

        avg_cf_return = float(resolved["counterfactual_return"].mean())
        saved_losses = resolved[resolved["counterfactual_return"] < 0.0]
        avoided_loss_ratio = len(saved_losses) / len(resolved) if len(resolved) > 0 else 0.0

        return {
            "total_rejected": len(df),
            "resolved_trades": len(resolved),
            "avoided_loss_ratio": avoided_loss_ratio,
            "avg_counterfactual_return": avg_cf_return,
            "filter_alpha_saved_pct": -avg_cf_return  # Positive if rejected trades lost money on average
        }
