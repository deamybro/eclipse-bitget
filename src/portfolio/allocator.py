"""
src/portfolio/allocator.py - Master Robust Allocator.
Combines HRP base weights, Alpha Credibility, Regime Fit, and Risk Throttles.
Enforces cash preservation when signals fail statistical scrutiny.
"""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from src.contracts import (
    AlphaSleeve, CapitalStatus, CredibilityReport, AlphaSignal,
    PortfolioAllocation, RegimeState
)
from src.portfolio.hrp import HierarchicalRiskParity
from src.portfolio.risk import RiskGovernor
from src.portfolio.no_trade_band import NoTradeBandFilter


class RobustPortfolioAllocator:
    """Institutional multi-sleeve risk and alpha allocator."""

    def __init__(
        self,
        hrp: Optional[HierarchicalRiskParity] = None,
        risk_governor: Optional[RiskGovernor] = None,
        no_trade_band: Optional[NoTradeBandFilter] = None,
        min_cash_buffer: float = 0.15,
        max_sleeve_weight: float = 0.45
    ):
        self.hrp = hrp or HierarchicalRiskParity()
        self.risk_governor = risk_governor or RiskGovernor()
        self.no_trade_band = no_trade_band or NoTradeBandFilter()
        self.min_cash_buffer = min_cash_buffer
        self.max_sleeve_weight = max_sleeve_weight
        self.current_weights: Dict[str, float] = {
            AlphaSleeve.PARALLAX.value: 0.0,
            AlphaSleeve.SHOCKWAVE.value: 0.0,
            AlphaSleeve.CARRY.value: 0.0,
            "CASH": 1.0
        }

    def allocate(
        self,
        timestamp_utc: datetime,
        current_equity: float,
        realized_vol: float,
        active_signals: Dict[str, AlphaSignal],
        credibility_reports: Dict[str, CredibilityReport],
        regime_state: RegimeState,
        historical_sleeve_returns: pd.DataFrame
    ) -> PortfolioAllocation:
        # 1. Base HRP weights
        hrp_weights = self.hrp.allocate(historical_sleeve_returns)

        # 2. Credibility Multipliers:
        # FULL_RISK: 1.0, REDUCED_RISK: 0.5, WATCH: 0.25, DISABLED: 0.0, INSUFFICIENT_EVIDENCE: 0.0
        cred_multipliers = {}
        for sleeve_name in [AlphaSleeve.PARALLAX.value, AlphaSleeve.SHOCKWAVE.value, AlphaSleeve.CARRY.value]:
            rep = credibility_reports.get(sleeve_name)
            if rep is None or rep.capital_status == CapitalStatus.DISABLED:
                cred_multipliers[sleeve_name] = 0.0
            elif rep.capital_status == CapitalStatus.FULL_RISK:
                cred_multipliers[sleeve_name] = 1.0
            elif rep.capital_status == CapitalStatus.REDUCED_RISK:
                cred_multipliers[sleeve_name] = 0.50
            elif rep.capital_status == CapitalStatus.WATCH:
                cred_multipliers[sleeve_name] = 0.25
            else:
                cred_multipliers[sleeve_name] = 0.0

        # 3. Active Signal Eligibility Multiplier
        signal_multipliers = {}
        for sleeve_name in [AlphaSleeve.PARALLAX.value, AlphaSleeve.SHOCKWAVE.value, AlphaSleeve.CARRY.value]:
            sig = active_signals.get(sleeve_name)
            if sig is not None and sig.eligible and sig.expected_net_edge > 0.0:
                # Scaled by confidence in edge
                signal_multipliers[sleeve_name] = min(1.5, 1.0 + sig.expected_net_edge * 10.0)
            else:
                signal_multipliers[sleeve_name] = 0.0

        # 4. Regime Fit Multipliers
        regime_fit = {
            AlphaSleeve.PARALLAX.value: regime_state.probabilities.get("Low-Vol Dispersion", 0.33),
            AlphaSleeve.SHOCKWAVE.value: regime_state.probabilities.get("High-Vol Dislocation", 0.33),
            AlphaSleeve.CARRY.value: regime_state.probabilities.get("Stable Basis Carry", 0.33)
        }

        # 5. Composite Sizing: HRP * Credibility * Signal * RegimeFit
        raw_weights = {}
        for s in [AlphaSleeve.PARALLAX.value, AlphaSleeve.SHOCKWAVE.value, AlphaSleeve.CARRY.value]:
            base_w = hrp_weights.get(s, 0.33)
            cm = cred_multipliers.get(s, 0.0)
            sm = signal_multipliers.get(s, 0.0)
            rf = max(0.2, regime_fit.get(s, 0.33))
            raw_w = base_w * cm * sm * rf
            raw_weights[s] = min(self.max_sleeve_weight, raw_w)

        # 6. Risk Scaling: Volatility Targeting & Drawdown Throttle
        vol_scalar = self.risk_governor.compute_vol_scalar(realized_vol)
        dd_scalar, dd_status = self.risk_governor.compute_drawdown_throttle(current_equity)
        overall_risk_scalar = vol_scalar * dd_scalar

        scaled_weights = {}
        for s, w in raw_weights.items():
            scaled_weights[s] = float(w * overall_risk_scalar)

        # 7. Cash Buffer Accounting
        total_sleeve_weight = sum(scaled_weights.values())
        max_allowed_sleeve_total = 1.0 - self.min_cash_buffer

        if total_sleeve_weight > max_allowed_sleeve_total:
            # Rescale sleeves to preserve cash buffer
            scale_down = max_allowed_sleeve_total / total_sleeve_weight
            for s in scaled_weights:
                scaled_weights[s] *= scale_down
            cash_w = self.min_cash_buffer
        else:
            cash_w = 1.0 - total_sleeve_weight

        scaled_weights["CASH"] = cash_w

        # 8. No-Trade Band Filter
        rebal_needed, final_weights = self.no_trade_band.should_rebalance(
            self.current_weights, scaled_weights
        )
        if rebal_needed:
            self.current_weights = final_weights

        gross_exp = sum(v for k, v in final_weights.items() if k != "CASH")
        net_exp = gross_exp  # Delta-neutral sleeve offsets can be decomposed

        return PortfolioAllocation(
            timestamp_utc=timestamp_utc,
            allocations=final_weights,
            cash_weight=final_weights.get("CASH", 1.0),
            gross_exposure=gross_exp,
            net_exposure=net_exp,
            rebalance_executed=rebal_needed,
            volatility_target_scalar=vol_scalar,
            drawdown_throttle_scalar=dd_scalar
        )
