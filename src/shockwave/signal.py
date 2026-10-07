"""
src/shockwave/signal.py - SHOCKWAVE Cross-Asset Dislocation Signal Engine.
Monitors factor residuals, tests mean-reversion stationarity, applies event firewall,
and generates structured AlphaSignal models.
"""

from datetime import datetime
import numpy as np

from src.contracts import AlphaSignal, AlphaSleeve, SignalDirection, EdgeEnvelope, DataQuality
from src.shockwave.factor_model import DynamicRollingFactorModel
from src.shockwave.half_life import ResidualHalfLifeEstimator
from src.shockwave.qwen_classifier import QwenEventClassifier, EventClassification
from src.execution.costs import CostEstimator


class ShockwaveSignalEngine:
    """Generates cross-asset residual / liquidity dislocation alpha signals."""

    def __init__(
        self,
        cost_estimator: CostEstimator | None = None,
        z_threshold: float = 2.0,
        min_edge_bps: float = 12.0,
        qwen_classifier: QwenEventClassifier | None = None
    ):
        self.cost_estimator = cost_estimator or CostEstimator()
        self.z_threshold = z_threshold
        self.min_edge_bps = min_edge_bps
        self.qwen_classifier = qwen_classifier or QwenEventClassifier()
        
        self.factor_models: dict[str, DynamicRollingFactorModel] = {}
        self.half_life_estimator = ResidualHalfLifeEstimator()
        self.residual_buffers: dict[str, list[float]] = {}

    def process_bar(
        self,
        symbol: str,
        timestamp_utc: datetime,
        rtoken_return: float,
        perp_return: float,
        btc_return: float,
        eth_return: float,
        bar_turnover: float,
        volatility: float,
        signal_id: str,
        is_fundamental_event: bool = False,
        headline: str | None = None
    ) -> AlphaSignal:
        if symbol not in self.factor_models:
            self.factor_models[symbol] = DynamicRollingFactorModel()
            self.residual_buffers[symbol] = []

        fm = self.factor_models[symbol]
        buf = self.residual_buffers[symbol]

        # 1. Update rolling factor model
        fm_res = fm.update(rtoken_return, perp_return, btc_return, eth_return)
        residual = fm_res["residual"]
        buf.append(residual)
        if len(buf) > 120:
            buf.pop(0)

        # 2. Residual statistics
        if len(buf) >= 24:
            res_arr = np.array(buf)
            res_std = float(np.std(res_arr))
            z_score = float(residual / res_std) if res_std > 1e-6 else 0.0
        else:
            res_std = 0.01
            z_score = 0.0

        # 3. Half-life mean-reversion check
        hl_diag = self.half_life_estimator.estimate(buf)
        is_mean_reverting = hl_diag["is_mean_reverting"]

        # 4. Expected Costs & Envelope
        expected_cost_bps = self.cost_estimator.estimate_round_trip_cost_bps(
            asset_type="spot",
            order_notional=10_000.0,
            bar_turnover=bar_turnover,
            volatility=volatility
        )

        raw_edge_bps = abs(residual) * 10000.0
        net_edge_bps = raw_edge_bps - expected_cost_bps

        envelope = EdgeEnvelope(
            point_edge=raw_edge_bps / 10000.0,
            lower_edge=max(0.0, (raw_edge_bps - 1.96 * res_std * 10000.0) / 10000.0),
            upper_edge=(raw_edge_bps + 1.96 * res_std * 10000.0) / 10000.0,
            interval_width=(1.96 * res_std * 10000.0),
            coverage_target=0.90,
            calibration_sample_count=len(buf),
            quality=DataQuality.DERIVED
        )

        direction = SignalDirection.NO_TRADE
        eligible = False
        rejection_reason = None

        # SHOCKWAVE Decision Logic:
        # If headline provided, evaluate via Qwen 3.8 Max event classifier
        qwen_diag = None
        if headline and not is_fundamental_event:
            qwen_res = self.qwen_classifier.classify_headline(symbol, headline)
            qwen_diag = qwen_res.model_dump()
            if qwen_res.is_fundamental_shock:
                is_fundamental_event = True
                rejection_reason = f"QWEN_FIREWALL_BLOCK_{qwen_res.event_type.upper()}"

        # If fundamental event detected (earnings, SEC 8-K), FIREWALL ACTIVE: DO NOT FADE!
        if is_fundamental_event:
            if not rejection_reason:
                rejection_reason = "FUNDAMENTAL_EVENT_FIREWALL_ACTIVE"
        elif not is_mean_reverting:
            rejection_reason = f"RESIDUAL_NOT_MEAN_REVERTING_{hl_diag['reason']}"
        elif abs(z_score) < self.z_threshold:
            rejection_reason = "RESIDUAL_INSIDE_NORMAL_BAND"
        elif raw_edge_bps < (expected_cost_bps + self.min_edge_bps):
            rejection_reason = "EDGE_BELOW_COST_PLUS_MINIMUM"
        else:
            # Trade mean reversion: if residual is deeply negative, rToken dropped abnormally -> BUY
            # If residual is deeply positive, rToken spiked abnormally -> SELL
            if z_score < -self.z_threshold:
                direction = SignalDirection.LONG
                eligible = True
            elif z_score > self.z_threshold:
                direction = SignalDirection.SHORT
                eligible = True

        return AlphaSignal(
            signal_id=signal_id,
            sleeve=AlphaSleeve.SHOCKWAVE,
            symbol=symbol,
            timestamp_utc=timestamp_utc,
            direction=direction,
            point_edge=raw_edge_bps / 10000.0,
            edge_envelope=envelope,
            expected_convergence=raw_edge_bps / 10000.0,
            expected_cost=expected_cost_bps / 10000.0,
            expected_net_edge=net_edge_bps / 10000.0,
            eligible=eligible,
            rejection_reason=rejection_reason,
            metadata={
                "z_score": z_score,
                "half_life_hours": hl_diag["half_life_hours"],
                "phi": hl_diag["phi"],
                "is_mean_reverting": is_mean_reverting,
                "betas": fm_res["betas"],
                "qwen_classification": qwen_diag
            }
        )
