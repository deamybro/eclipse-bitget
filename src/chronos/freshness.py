"""
src/chronos/freshness.py - Staleness Monitoring & Reference Aging.
Tracks observation age, detects broken data pipelines, and calculates variance
inflation factors for stale references when the underlying cash equity is closed.
"""

from datetime import datetime
from src.contracts import DataQuality


class FreshnessMonitor:
    """Evaluates reference data freshness and computes uncertainty penalties."""

    def __init__(self, stale_threshold_seconds: float = 3600.0):
        self.stale_threshold_seconds = stale_threshold_seconds

    def evaluate_freshness(
        self,
        current_time_utc: datetime,
        source_time_utc: datetime,
        underlying_open: bool
    ) -> dict:
        """
        Computes reference age and determines whether observation is fresh or stale.
        If underlying is closed, observation is retained as a stale anchor with
        variance penalty.
        """
        age_seconds = max(0.0, (current_time_utc - source_time_utc).total_seconds())
        is_stale = age_seconds > self.stale_threshold_seconds

        # Variance inflation factor for Kalman filter or residual tracking
        # When market is closed, uncertainty grows with square root of time
        if not underlying_open:
            hours_elapsed = age_seconds / 3600.0
            variance_inflation = 1.0 + 0.25 * (hours_elapsed ** 0.5)
            quality = DataQuality.PROXY
        elif is_stale:
            variance_inflation = 2.5
            quality = DataQuality.PROXY
        else:
            variance_inflation = 1.0
            quality = DataQuality.OBSERVED

        return {
            "reference_age_seconds": age_seconds,
            "is_stale": is_stale,
            "underlying_open": underlying_open,
            "variance_inflation_factor": variance_inflation,
            "quality": quality
        }
