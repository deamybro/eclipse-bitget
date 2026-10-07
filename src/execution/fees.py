"""
src/execution/fees.py - Realistic Exchange Fee Schedules.
Implements exact Bitget fee structures for Spot and Equity Perpetuals.
"""

from typing import Literal


class FeeModel:
    """Computes exact trading fees based on asset type and execution side."""

    def __init__(
        self,
        spot_maker_bps: float = 10.0,
        spot_taker_bps: float = 10.0,
        perp_maker_bps: float = 2.0,
        perp_taker_bps: float = 6.0
    ):
        self.spot_maker_rate = spot_maker_bps / 10000.0
        self.spot_taker_rate = spot_taker_bps / 10000.0
        self.perp_maker_rate = perp_maker_bps / 10000.0
        self.perp_taker_rate = perp_taker_bps / 10000.0

    def compute_fee(
        self,
        notional: float,
        asset_type: Literal["spot", "perp"],
        order_style: Literal["maker", "taker"] = "taker"
    ) -> float:
        """Calculates absolute dollar fee for an executed fill."""
        if asset_type == "spot":
            rate = self.spot_maker_rate if order_style == "maker" else self.spot_taker_rate
        else:
            rate = self.perp_maker_rate if order_style == "maker" else self.perp_taker_rate
        return abs(notional) * rate
