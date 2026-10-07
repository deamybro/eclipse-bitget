"""
src/proof/cost_stress.py - Execution Cost Stress Test Engine.
Evaluates strategy return and Sharpe decay across a friction grid: 1.0x, 1.25x, 1.5x, 2.0x.
"""

from typing import Dict, Any, List
import pandas as pd


class CostStressTester:
    """Stress tests performance degradation under elevated transaction friction."""

    @staticmethod
    def run_stress_grid(
        base_metrics: Dict[str, float],
        stress_multipliers: List[float] = [1.0, 1.25, 1.5, 2.0]
    ) -> pd.DataFrame:
        base_sharpe = base_metrics.get("sharpe", 1.8)
        base_ret = base_metrics.get("annualized_return", 0.25)
        base_vol = base_metrics.get("annualized_volatility", 0.12)

        rows = []
        for sm in stress_multipliers:
            # Friction penalty scales linearly with cost multiplier
            cost_penalty_pct = 0.03 * (sm - 1.0)
            stressed_ret = base_ret - cost_penalty_pct
            stressed_sharpe = max(0.0, (stressed_ret - 0.04) / max(1e-6, base_vol))
            
            rows.append({
                "Stress Multiplier": f"{sm:.2f}x",
                "Net Annual Return (%)": stressed_ret * 100.0,
                "Stressed Sharpe": stressed_sharpe,
                "Sharpe Decay (%)": ((base_sharpe - stressed_sharpe) / base_sharpe * 100.0) if base_sharpe > 0 else 0.0,
                "Alpha Survives": stressed_sharpe > 0.5
            })

        return pd.DataFrame(rows)
