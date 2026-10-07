"""
src/proof/rolling.py - Rolling Metric Stability & Regime Analysis.
Computes rolling 30-day (720-hour) Sharpe, volatility, and drawdown windows.
"""

import numpy as np
import pandas as pd


def compute_rolling_metrics(equity_series: pd.Series, window_hours: int = 720) -> pd.DataFrame:
    """
    Computes rolling metrics over a sliding window (default 30 days = 720 hours).
    """
    returns = equity_series.pct_change().fillna(0.0)
    ann_factor = 8760.0

    rolling_mean = returns.rolling(window_hours).mean() * ann_factor
    rolling_vol = returns.rolling(window_hours).std() * np.sqrt(ann_factor)
    rolling_sharpe = (rolling_mean - 0.04) / np.maximum(1e-6, rolling_vol)

    cummax = equity_series.rolling(window_hours, min_periods=1).max()
    rolling_dd = (cummax - equity_series) / np.maximum(1e-6, cummax)

    df = pd.DataFrame({
        "equity": equity_series,
        "rolling_sharpe": rolling_sharpe,
        "rolling_vol": rolling_vol,
        "rolling_drawdown": rolling_dd
    })
    return df
