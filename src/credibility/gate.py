"""
src/credibility/gate.py - Alpha Credibility Gate Engine.
Evaluates OOS degradation, DSR, PBO, stability, and assigns capital risk tiers.
"""

from src.contracts import AlphaSleeve, CapitalStatus, CredibilityReport
from src.credibility.deflated_sharpe import compute_deflated_sharpe_ratio
from src.credibility.pbo import compute_cscv_pbo


class AlphaCredibilityGate:
    """Evaluates whether an alpha sleeve's live/OOS metrics deserve risk budget."""

    def __init__(
        self,
        min_trade_count: int = 15,
        min_oos_is_ratio: float = 0.50,
        min_deflated_sharpe: float = 0.85,
        max_pbo: float = 0.40
    ):
        self.min_trade_count = min_trade_count
        self.min_oos_is_ratio = min_oos_is_ratio
        self.min_deflated_sharpe = min_deflated_sharpe
        self.max_pbo = max_pbo

    def evaluate_sleeve(
        self,
        sleeve: AlphaSleeve,
        is_sharpe: float,
        oos_sharpe: float,
        sortino: float,
        max_drawdown: float,
        trade_count: int,
        rolling_sharpe_stability: float,
        parameter_stability: float,
        cost_survival_ratio: float,
        signal_ic: float,
        sample_length: int,
        n_tested_trials: int = 10,
        sharpe_variance: float = 0.15,
        pbo_score: float = 0.20
    ) -> CredibilityReport:
        # Sample adequacy
        sample_adequate = trade_count >= self.min_trade_count

        # OOS / IS ratio
        ratio = (oos_sharpe / is_sharpe) if is_sharpe > 0 else 0.0

        # Deflated Sharpe Ratio
        dsr = compute_deflated_sharpe_ratio(
            observed_sharpe=max(0.0, oos_sharpe),
            sample_length=sample_length,
            n_trials=n_tested_trials,
            variance_sharpes=sharpe_variance
        )

        # Capital Status Assignment
        if not sample_adequate:
            status = CapitalStatus.INSUFFICIENT_EVIDENCE
            decay_status = "INSUFFICIENT_DATA"
        elif oos_sharpe <= 0 or cost_survival_ratio <= 0.0:
            status = CapitalStatus.DISABLED
            decay_status = "BROKEN"
        elif ratio < self.min_oos_is_ratio or dsr < 0.70 or pbo_score > self.max_pbo:
            status = CapitalStatus.REDUCED_RISK
            decay_status = "WEAKENING"
        elif ratio >= 0.80 and dsr >= self.min_deflated_sharpe and pbo_score <= 0.25:
            status = CapitalStatus.FULL_RISK
            decay_status = "HEALTHY"
        else:
            status = CapitalStatus.WATCH
            decay_status = "DECAYING"

        return CredibilityReport(
            sleeve=sleeve,
            in_sample_sharpe=is_sharpe,
            out_of_sample_sharpe=oos_sharpe,
            oos_is_ratio=ratio,
            sortino=sortino,
            max_drawdown=max_drawdown,
            rolling_sharpe_stability=rolling_sharpe_stability,
            deflated_sharpe=dsr,
            pbo=pbo_score,
            parameter_stability=parameter_stability,
            cost_survival_ratio=cost_survival_ratio,
            signal_ic=signal_ic,
            recent_decay_status=decay_status,
            trade_count=trade_count,
            sample_adequate=sample_adequate,
            capital_status=status
        )
