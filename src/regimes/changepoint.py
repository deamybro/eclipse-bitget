"""
src/regimes/changepoint.py - Online Structural Break Detector (CUSUM Engine).
Detects rapid regime transitions and variance shifts to trigger defensive risk throttles.
"""

import numpy as np


class OnlineCUSUMBreakDetector:
    """Two-sided cumulative sum (CUSUM) change-point detector."""

    def __init__(self, drift: float = 0.5, threshold: float = 5.0):
        self.drift = drift
        self.threshold = threshold
        self.s_pos = 0.0
        self.s_neg = 0.0
        self.history = []

    def update(self, value: float) -> tuple[bool, float]:
        """
        Updates cumulative sum with new standardized observation.
        Returns (is_break_detected, current_test_statistic).
        """
        self.history.append(value)
        if len(self.history) < 15:
            return False, 0.0

        mean = np.mean(self.history[-30:])
        std = np.std(self.history[-30:]) + 1e-8
        z = (value - mean) / std

        self.s_pos = max(0.0, self.s_pos + z - self.drift)
        self.s_neg = max(0.0, self.s_neg - z - self.drift)

        stat = max(self.s_pos, self.s_neg)
        break_detected = stat > self.threshold

        if break_detected:
            # Partially reset after firing
            self.s_pos = self.threshold * 0.5
            self.s_neg = self.threshold * 0.5

        return break_detected, float(stat)
