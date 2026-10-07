"""
src/uncertainty/conformal.py - Causal Sequential Time-Series Conformal Prediction.
Calibrates empirical uncertainty intervals using only historical past forecast errors,
strictly avoiding random permutation and future residual leakage.
"""

import numpy as np


class SequentialConformalCalibrator:
    """
    Time-Series Conformal Prediction Interval:
    Maintains a rolling/expanding calibration buffer of past absolute forecast errors |y_t - y_hat_t|.
    Computes (1 - alpha) empirical quantile to construct rigorous prediction intervals.
    """

    def __init__(self, coverage_target: float = 0.90, min_history: int = 20, max_history: int = 250):
        self.coverage_target = coverage_target
        self.min_history = min_history
        self.max_history = max_history
        self.past_errors: list[float] = []

    def update(self, absolute_error: float):
        """Appends contemporaneous realized error to calibration buffer."""
        self.past_errors.append(abs(absolute_error))
        if len(self.past_errors) > self.max_history:
            self.past_errors.pop(0)

    def compute_interval(self, point_forecast: float) -> tuple[float, float, float, bool]:
        """
        Returns (lower_bound, upper_bound, interval_width, is_calibrated).
        Uses causal empirical quantile strictly from past errors.
        """
        if len(self.past_errors) < self.min_history:
            # Insufficient history: return wide conservative fallback
            fallback_width = max(0.01, abs(point_forecast) * 0.5)
            return (
                point_forecast - fallback_width,
                point_forecast + fallback_width,
                2.0 * fallback_width,
                False
            )

        # Compute empirical quantile (1 - alpha)
        # Using conformal quantile formula: ceil((n + 1) * (1 - alpha)) / n
        n = len(self.past_errors)
        q_idx = int(np.ceil((n + 1) * self.coverage_target) / n * (n - 1))
        q_idx = min(n - 1, max(0, q_idx))
        
        sorted_errors = np.sort(self.past_errors)
        radius = float(sorted_errors[q_idx])

        lower = point_forecast - radius
        upper = point_forecast + radius
        width = 2.0 * radius

        return lower, upper, width, True
