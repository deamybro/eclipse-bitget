"""
src/uta/effective_capital.py - Bitget Piecewise Tiered Collateral Engine.
Calculates piecewise effective collateral value and marginal capital efficiency:
Marginal Efficiency = d(EffectiveCollateral) / d(NominalNotional).
"""

from typing import List, Dict
from pydantic import BaseModel


class TierSpecification(BaseModel):
    min_notional: float
    max_notional: float
    ratio: float  # e.g. 0.90 for 10% haircut


class UTACapitalEngine:
    """Computes piecewise tiered collateral valuations and marginal efficiencies."""

    def __init__(self, tiers: List[Dict[str, float]] | None = None):
        if tiers:
            self.tiers = [TierSpecification(**t) for t in tiers]
        else:
            # Default verified Bitget rToken schedule
            self.tiers = [
                TierSpecification(min_notional=0.0, max_notional=100_000.0, ratio=0.90),
                TierSpecification(min_notional=100_000.0, max_notional=500_000.0, ratio=0.80),
                TierSpecification(min_notional=500_000.0, max_notional=2_000_000.0, ratio=0.70),
                TierSpecification(min_notional=2_000_000.0, max_notional=float("inf"), ratio=0.50),
            ]

    def compute_effective_collateral(self, nominal_notional: float) -> float:
        """Piecewise tiered valuation of nominal holding."""
        remaining = nominal_notional
        effective_value = 0.0

        for tier in self.tiers:
            tier_capacity = tier.max_notional - tier.min_notional
            chunk = min(remaining, tier_capacity)
            if chunk > 0:
                effective_value += chunk * tier.ratio
                remaining -= chunk
            if remaining <= 0:
                break

        return float(effective_value)

    def compute_marginal_efficiency(self, current_notional: float, delta_notional: float = 1_000.0) -> float:
        """
        Computes marginal capital efficiency = Delta Effective / Delta Nominal
        when adding delta_notional to current_notional.
        """
        c1 = self.compute_effective_collateral(current_notional)
        c2 = self.compute_effective_collateral(current_notional + delta_notional)
        return float((c2 - c1) / delta_notional)

    def compute_roec(self, expected_net_alpha_dollars: float, marginal_effective_capital: float) -> float:
        """
        Return on Effective Capital: ROEC = Net Alpha / Marginal Capital Consumed.
        """
        if marginal_effective_capital <= 0.0:
            return 0.0
        return float(expected_net_alpha_dollars / marginal_effective_capital)
