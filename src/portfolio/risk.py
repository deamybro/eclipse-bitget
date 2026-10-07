"""
src/portfolio/risk.py - Portfolio Volatility Targeting & Drawdown Throttles.
Enforces deterministic risk reduction and capital preservation tiers.
"""

import numpy as np


class RiskGovernor:
    """Manages gross exposure scaling, volatility targeting, and drawdown throttling."""

    def __init__(
        self,
        target_annualized_vol: float = 0.12,
        max_gross_leverage: float = 1.5,
        dd_tier1_threshold: float = 0.03,  # 3% drawdown -> 70% risk
        dd_tier2_threshold: float = 0.06,  # 6% drawdown -> 40% risk
        dd_hard_stop: float = 0.10         # 10% drawdown -> 0% risk (Freeze)
    ):
        self.target_vol = target_annualized_vol
        self.max_gross = max_gross_leverage
        self.dd_tier1 = dd_tier1_threshold
        self.dd_tier2 = dd_tier2_threshold
        self.dd_hard_stop = dd_hard_stop
        self.peak_equity = 100_000.0

    def compute_vol_scalar(self, realized_vol: float) -> float:
        """Computes causal volatility targeting scalar = target_vol / realized_vol."""
        vol = max(realized_vol, 0.04)
        raw_scalar = self.target_vol / vol
        # Bound scalar between 0.25 and max_gross
        return float(np.clip(raw_scalar, 0.25, self.max_gross))

    def compute_drawdown_throttle(self, current_equity: float) -> tuple[float, str]:
        """
        Computes deterministic drawdown multiplier and status.
        """
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        dd = (self.peak_equity - current_equity) / self.peak_equity if self.peak_equity > 0 else 0.0

        if dd >= self.dd_hard_stop:
            return 0.0, "HARD_FREEZE_100_CASH"
        elif dd >= self.dd_tier2:
            return 0.40, "TIER2_STRONG_REDUCTION"
        elif dd >= self.dd_tier1:
            return 0.70, "TIER1_MODERATE_REDUCTION"
        else:
            return 1.0, "NORMAL"
