"""
src/execution/costs.py - Comprehensive Round-Trip Cost Estimator.
Calculates total friction including fees, expected slippage, and legging penalties.
"""

from src.execution.fees import FeeModel
from src.execution.slippage import MarketImpactModel


class CostEstimator:
    """Combines fee schedules, market impact, and friction buffers."""

    def __init__(
        self,
        fee_model: FeeModel | None = None,
        impact_model: MarketImpactModel | None = None,
        paired_leg_penalty_bps: float = 2.5
    ):
        self.fee_model = fee_model or FeeModel()
        self.impact_model = impact_model or MarketImpactModel()
        self.paired_leg_penalty_bps = paired_leg_penalty_bps

    def estimate_round_trip_cost_bps(
        self,
        asset_type: str,  # spot, perp, or pair
        order_notional: float,
        bar_turnover: float,
        volatility: float,
        stress_multiplier: float = 1.0
    ) -> float:
        """
        Estimates total round-trip cost in basis points (entry + exit).
        """
        if asset_type == "pair":
            # Multi-leg trade: Spot leg + Perp leg + legging risk
            spot_fee_bps = (self.fee_model.spot_taker_rate * 2) * 10000.0  # entry + exit
            perp_fee_bps = (self.fee_model.perp_taker_rate * 2) * 10000.0
            
            spot_slip = self.impact_model.compute_slippage_bps(
                order_notional / 2, bar_turnover, volatility, stress_multiplier
            ) * 2
            perp_slip = self.impact_model.compute_slippage_bps(
                order_notional / 2, bar_turnover, volatility, stress_multiplier
            ) * 2
            
            total_bps = spot_fee_bps + perp_fee_bps + spot_slip + perp_slip + self.paired_leg_penalty_bps
        else:
            fee_bps = (
                (self.fee_model.spot_taker_rate * 2) if asset_type == "spot"
                else (self.fee_model.perp_taker_rate * 2)
            ) * 10000.0
            slip_bps = self.impact_model.compute_slippage_bps(
                order_notional, bar_turnover, volatility, stress_multiplier
            ) * 2
            total_bps = fee_bps + slip_bps

        return float(total_bps)

    def calculate_breakeven_friction(self, gross_alpha_bps: float) -> float:
        """Computes maximum tolerable friction in bps before strategy PnL goes negative."""
        return max(0.0, gross_alpha_bps)
