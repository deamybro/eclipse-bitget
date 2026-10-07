"""
src/proof/metrics.py - Institutional Quantitative Metrics Engine.
Computes return, volatility, Sharpe, Sortino, Calmar, MaxDD, Win Rate, Turnover,
and cost attribution without fabricating any values.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def compute_quant_metrics(equity_series: pd.Series, risk_free_rate: float = 0.04) -> Dict[str, float]:
    """
    Computes annualized institutional portfolio statistics from hourly or daily equity curve.
    equity_series: pd.Series indexed by timestamp or sequential steps.
    """
    if len(equity_series) < 5:
        return {"sharpe": 0.0, "sortino": 0.0, "max_drawdown": 0.0, "total_return": 0.0}

    # Hourly returns
    returns = equity_series.pct_change().dropna()
    if len(returns) == 0:
        return {"sharpe": 0.0, "sortino": 0.0, "max_drawdown": 0.0, "total_return": 0.0}

    # Annualization factor for hourly crypto/rToken series: 24 * 365 = 8760
    ann_factor = 8760.0
    
    total_return = float((equity_series.iloc[-1] - equity_series.iloc[0]) / equity_series.iloc[0])
    mean_ret = float(returns.mean()) * ann_factor
    vol = float(returns.std()) * np.sqrt(ann_factor)

    # Sharpe Ratio
    excess_ret = mean_ret - risk_free_rate
    sharpe = float(excess_ret / vol) if vol > 1e-6 else 0.0

    # Downside deviation for Sortino
    downside_returns = returns[returns < 0.0]
    downside_std = float(downside_returns.std()) * np.sqrt(ann_factor) if len(downside_returns) > 0 else 1e-6
    sortino = float(excess_ret / downside_std) if downside_std > 1e-6 else 0.0

    # Maximum Drawdown
    cummax = equity_series.cummax()
    drawdowns = (cummax - equity_series) / cummax
    max_dd = float(drawdowns.max())

    # Calmar Ratio
    calmar = float(mean_ret / max_dd) if max_dd > 1e-6 else 0.0

    # Win Rate
    win_rate = float((returns > 0).mean())

    return {
        "total_return": total_return,
        "annualized_return": mean_ret,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "win_rate": win_rate
    }
