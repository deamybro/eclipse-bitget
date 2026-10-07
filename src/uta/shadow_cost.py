"""
src/uta/shadow_cost.py - Internal Collateral Opportunity Cost Estimator.
ECLIPSE internal portfolio metric (NOT an exchange fee).
Estimates opportunity cost of consuming scarce effective collateral margin.
"""


class CollateralShadowCostEstimator:
    """Computes internal opportunity cost penalty for low-haircut efficiency allocations."""

    def __init__(self, hurdle_rate_annual: float = 0.08):
        self.hurdle_rate_per_hour = hurdle_rate_annual / (365.0 * 24.0)

    def compute_shadow_cost_bps(
        self,
        nominal_notional: float,
        marginal_efficiency: float,
        holding_hours: float = 24.0
    ) -> float:
        """
        Penalty = (1.0 - marginal_efficiency) * hurdle_rate * holding_hours * 10,000 bps.
        If an asset only provides 70% collateral credit, 30% haircut consumes liquidity.
        """
        haircut = max(0.0, 1.0 - marginal_efficiency)
        opportunity_loss = haircut * (self.hurdle_rate_per_hour * holding_hours)
        return float(opportunity_loss * 10000.0)
