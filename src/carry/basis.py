"""
src/carry/basis.py - Basis Dynamics & Multiplier Hedge Ratio Engine.
Computes consistent log basis ln(P_perp / P_rtoken) and adjusts for contract multipliers.
"""

import numpy as np


class BasisCalculator:
    """Computes exact contract-adjusted basis dynamics."""

    def __init__(self, contract_multiplier: float = 0.01):
        # Bitget equity perp multiplier: 0.01 (100 contracts = 1 share)
        self.contract_multiplier = contract_multiplier

    def compute_log_basis(self, rtoken_price: float, perp_price: float) -> float:
        """Returns ln(P_perp / P_rtoken)."""
        if rtoken_price <= 0 or perp_price <= 0:
            return 0.0
        return float(np.log(perp_price / rtoken_price))

    def compute_hedge_ratio(self, rtoken_shares: float) -> float:
        """
        Calculates required perpetual contracts to hedge rToken shares:
        Contracts = shares / multiplier (e.g. 10 shares / 0.01 = 1,000 contracts).
        """
        return float(rtoken_shares / self.contract_multiplier)
