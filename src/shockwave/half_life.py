"""
src/shockwave/half_life.py - Ornstein-Uhlenbeck Residual Mean-Reversion Estimator.
Fits AR(1) process on historical factor residuals:
epsilon_t = phi * epsilon_{t-1} + eta_t
Derives estimated half-life t_1/2 = -ln(2) / ln(phi) if 0 < phi < 1.
"""

import numpy as np


class ResidualHalfLifeEstimator:
    """Estimates mean-reversion persistence of idiosyncratic dislocation residuals."""

    def __init__(self, max_half_life_hours: float = 48.0):
        self.max_half_life_hours = max_half_life_hours

    def estimate(self, residuals: list[float]) -> dict:
        """
        Fits AR(1) autoregression on residuals and returns half-life diagnostics.
        """
        if len(residuals) < 20:
            return {
                "is_mean_reverting": False,
                "half_life_hours": float("inf"),
                "phi": 1.0,
                "reason": "INSUFFICIENT_SAMPLE"
            }

        res = np.array(residuals)
        y = res[1:]
        x = res[:-1]

        # Simple OLS without intercept
        denom = np.sum(x ** 2)
        if denom < 1e-12:
            return {
                "is_mean_reverting": False,
                "half_life_hours": float("inf"),
                "phi": 1.0,
                "reason": "ZERO_VARIANCE"
            }

        phi = float(np.sum(x * y) / denom)

        # For stationary mean-reverting AR(1), 0 < phi < 1
        if 0.05 < phi < 0.98:
            half_life = float(-np.log(2.0) / np.log(phi))
            is_valid = half_life <= self.max_half_life_hours
            return {
                "is_mean_reverting": is_valid,
                "half_life_hours": half_life,
                "phi": phi,
                "reason": "VALID_MEAN_REVERSION" if is_valid else "HALF_LIFE_TOO_LONG"
            }
        else:
            return {
                "is_mean_reverting": False,
                "half_life_hours": float("inf"),
                "phi": phi,
                "reason": "NON_STATIONARY_RESIDUAL"
            }
