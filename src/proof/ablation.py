"""
src/proof/ablation.py - Systematic Component Ablation Engine.
Quantifies incremental value-add of each architectural module:
1. Equal Weight Baseline
2. HRP Only (no alpha tilts)
3. HRP + Credibility Gate
4. HRP + Regime Intelligence
5. FULL ECLIPSE (HRP + Credibility + Regimes + Edge Envelope + UTA)
"""

from typing import Dict, Any, List
import pandas as pd
from src.proof.metrics import compute_quant_metrics


class AblationEngine:
    """Runs automated ablation studies across portfolio configurations."""

    @staticmethod
    def evaluate_configurations(config_equity_curves: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        Takes a dict of {config_name: equity_series} and returns a comparative table.
        """
        rows = []
        for name, series in config_equity_curves.items():
            metrics = compute_quant_metrics(series)
            rows.append({
                "Configuration": name,
                "Total Return (%)": metrics["total_return"] * 100.0,
                "Annual Return (%)": metrics["annualized_return"] * 100.0,
                "Annual Vol (%)": metrics["annualized_volatility"] * 100.0,
                "Sharpe": metrics["sharpe"],
                "Sortino": metrics["sortino"],
                "Max DD (%)": metrics["max_drawdown"] * 100.0,
                "Calmar": metrics["calmar"]
            })

        df = pd.DataFrame(rows)
        return df
