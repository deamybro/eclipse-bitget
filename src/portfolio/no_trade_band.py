"""
src/portfolio/no_trade_band.py - Target Weight Tolerance & Turnover Dampening.
Prevents churn and unnecessary transaction friction by rebalancing only when
drift exceeds configured tolerance bands.
"""

from typing import Dict


class NoTradeBandFilter:
    """Filters target weight adjustments through deadband thresholds."""

    def __init__(self, band_pct: float = 0.03):
        # 3% drift band by default
        self.band_pct = band_pct

    def should_rebalance(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> tuple[bool, Dict[str, float]]:
        """
        Determines whether portfolio requires rebalancing.
        Returns (rebalance_needed, effective_weights).
        """
        all_keys = set(current_weights.keys()).union(set(target_weights.keys()))
        rebalance_needed = False

        for k in all_keys:
            cw = current_weights.get(k, 0.0)
            tw = target_weights.get(k, 0.0)
            if abs(tw - cw) > self.band_pct:
                rebalance_needed = True
                break

        if rebalance_needed:
            return True, target_weights
        else:
            return False, current_weights
