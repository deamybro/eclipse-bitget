"""
src/execution/slippage.py - Calibrated Market Impact & Slippage Models.
Implements square-root bar participation impact and stress test multipliers.
"""

import numpy as np


class MarketImpactModel:
    """
    Computes expected and realized slippage in basis points using:
    Impact (bps) = alpha * volatility * sqrt(order_notional / bar_turnover) * stress_multiplier
    """

    def __init__(
        self,
        base_alpha: float = 0.15,
        min_slippage_bps: float = 1.0,
        max_slippage_bps: float = 50.0
    ):
        self.base_alpha = base_alpha
        self.min_slippage_bps = min_slippage_bps
        self.max_slippage_bps = max_slippage_bps

    def compute_slippage_bps(
        self,
        order_notional: float,
        bar_turnover: float,
        volatility: float,
        stress_multiplier: float = 1.0
    ) -> float:
        """
        Calculates slippage in basis points.
        """
        turnover = max(bar_turnover, 1000.0)
        participation = min(1.0, abs(order_notional) / turnover)
        vol = max(volatility, 0.05)

        impact_bps = self.base_alpha * (vol * 10000.0) * np.sqrt(participation) * stress_multiplier
        # Bound slippage between min floor and max cap
        impact_bps = max(self.min_slippage_bps * stress_multiplier, min(self.max_slippage_bps, impact_bps))
        return float(impact_bps)

    def apply_slippage(
        self,
        base_price: float,
        side: str,  # BUY or SELL
        order_notional: float,
        bar_turnover: float,
        volatility: float,
        stress_multiplier: float = 1.0
    ) -> tuple[float, float]:
        """
        Returns (executed_price, slippage_bps).
        BUY orders slip upward, SELL orders slip downward.
        """
        slip_bps = self.compute_slippage_bps(order_notional, bar_turnover, volatility, stress_multiplier)
        slip_factor = slip_bps / 10000.0

        if side.upper() == "BUY":
            executed_price = base_price * (1.0 + slip_factor)
        else:
            executed_price = base_price * (1.0 - slip_factor)

        return executed_price, slip_bps
