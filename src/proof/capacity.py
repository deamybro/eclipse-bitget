"""
src/proof/capacity.py - Institutional Strategy Capacity Modeler.
Estimates net return and Sharpe degradation as AUM scales from $100k to $10M
under the calibrated non-linear square-root market impact model.
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd


class CapacityModeler:
    """Models performance decay as fund size increases participation rate."""

    @staticmethod
    def evaluate_capacity_curve(
        base_sharpe: float = 2.10,
        base_net_return: float = 0.28,
        typical_hourly_turnover: float = 2_000_000.0,
        aum_levels: List[float] = [100_000.0, 500_000.0, 2_000_000.0, 10_000_000.0]
    ) -> pd.DataFrame:
        rows = []
        for aum in aum_levels:
            # Typical trade size ~ 10% of portfolio rebalanced
            trade_size = aum * 0.10
            participation = trade_size / typical_hourly_turnover
            # Impact bps = alpha * sqrt(participation) * 100 bps
            impact_penalty = 0.05 * np.sqrt(min(1.0, participation))
            
            modeled_return = max(0.0, base_net_return - impact_penalty)
            modeled_sharpe = max(0.0, base_sharpe * (modeled_return / max(1e-6, base_net_return)))
            
            rows.append({
                "AUM ($)": f"${aum:,.0f}",
                "Typical Order ($)": f"${trade_size:,.0f}",
                "Participation Rate (%)": participation * 100.0,
                "Estimated Impact Penalty (%)": impact_penalty * 100.0,
                "Modelled Net Return (%)": modeled_return * 100.0,
                "Modelled Sharpe": modeled_sharpe,
                "Capacity Status": "OPTIMAL" if participation < 0.02 else ("VIABLE" if participation < 0.08 else "CONSTRAINED")
            })

        return pd.DataFrame(rows)
