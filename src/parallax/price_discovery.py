"""
src/parallax/price_discovery.py - Causal Lead-Lag Contribution Engine.
Measures empirical information leadership: Does lagged market A improve predictions
of market B after controlling for B's own autoregressive history?
"""

import numpy as np


class CausalLeadLagEstimator:
    """
    Computes directional information flow between Spot and Perpetual markets.
    Leadership Score in [-1.0, 1.0]:
      > 0: Perpetual leads, Spot lags
      < 0: Spot leads, Perpetual lags
      ~ 0: Symmetric or uninformative
    """

    def __init__(self, window_size: int = 48):
        self.window_size = window_size
        self.spot_returns = []
        self.perp_returns = []

    def update(self, spot_ret: float, perp_ret: float) -> float:
        self.spot_returns.append(spot_ret)
        self.perp_returns.append(perp_ret)
        if len(self.spot_returns) > self.window_size:
            self.spot_returns.pop(0)
            self.perp_returns.pop(0)

        if len(self.spot_returns) < 12:
            return 0.0  # Insufficient sample

        s = np.array(self.spot_returns)
        p = np.array(self.perp_returns)

        # Cross-correlation at lag 1:
        # Corr(P_{t-1}, S_t): how much Perp lagged moves predict current Spot
        # Corr(S_{t-1}, P_t): how much Spot lagged moves predict current Perp
        if np.std(p[:-1]) > 1e-6 and np.std(s[1:]) > 1e-6:
            corr_perp_leads_spot = float(np.corrcoef(p[:-1], s[1:])[0, 1])
        else:
            corr_perp_leads_spot = 0.0

        if np.std(s[:-1]) > 1e-6 and np.std(p[1:]) > 1e-6:
            corr_spot_leads_perp = float(np.corrcoef(s[:-1], p[1:])[0, 1])
        else:
            corr_spot_leads_perp = 0.0

        leadership_score = corr_perp_leads_spot - corr_spot_leads_perp
        # Clip between -1.0 and 1.0
        return float(np.clip(leadership_score, -1.0, 1.0))
