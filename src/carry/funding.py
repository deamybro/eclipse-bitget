"""
src/carry/funding.py - Funding Rate Persistence & Expected Yield Forecaster.
Fits causal autoregressive and exponential persistence models on 8-hour settlements.
"""

import numpy as np


class FundingPersistenceForecaster:
    """Estimates forward cumulative funding cash flow over an intended holding window."""

    def __init__(self, ewma_span: int = 15):
        self.ewma_span = ewma_span
        self.alpha = 2.0 / (ewma_span + 1.0)
        self.ewma_rate: float | None = None
        self.history: list[float] = []

    def update(self, latest_funding_rate: float) -> float:
        self.history.append(latest_funding_rate)
        if len(self.history) > 90:
            self.history.pop(0)

        if self.ewma_rate is None:
            self.ewma_rate = latest_funding_rate
        else:
            self.ewma_rate = self.alpha * latest_funding_rate + (1.0 - self.alpha) * self.ewma_rate

        return float(self.ewma_rate)

    def forecast_cumulative_funding(self, holding_periods: int = 6) -> float:
        """
        Forecasts expected funding cash flow over N settlement periods (e.g. 6 x 8h = 48 hours).
        """
        rate = self.ewma_rate if self.ewma_rate is not None else 0.0
        return float(rate * holding_periods)
