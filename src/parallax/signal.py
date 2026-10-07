"""
src/parallax/signal.py - PARALLAX Signal Generation Engine.
Fuses Kalman latent fair value, causal lead-lag discovery, and execution costs.
Generates typed AlphaSignal with explicit eligibility and rejection reasons.
"""

from datetime import datetime
from src.contracts import AlphaSignal, AlphaSleeve, SignalDirection, EdgeEnvelope, DataQuality
from src.parallax.latent_value import KalmanLatentPriceFilter
from src.parallax.price_discovery import CausalLeadLagEstimator
from src.execution.costs import CostEstimator


class ParallaxSignalEngine:
    """Generates information handoff / price-discovery alpha signals."""

    def __init__(
        self,
        cost_estimator: CostEstimator | None = None,
        min_edge_bps: float = 8.0,
        uncertainty_buffer_bps: float = 5.0
    ):
        self.cost_estimator = cost_estimator or CostEstimator()
        self.min_edge_bps = min_edge_bps
        self.uncertainty_buffer_bps = uncertainty_buffer_bps
        
        self.filters: dict[str, KalmanLatentPriceFilter] = {}
        self.lead_lag_estimators: dict[str, CausalLeadLagEstimator] = {}

    def process_bar(
        self,
        symbol: str,
        timestamp_utc: datetime,
        spot_price: float,
        perp_price: float,
        spot_return: float,
        perp_return: float,
        is_us_open: bool,
        reference_age_seconds: float,
        bar_turnover: float,
        volatility: float,
        signal_id: str
    ) -> AlphaSignal:
        if symbol not in self.filters:
            self.filters[symbol] = KalmanLatentPriceFilter()
            self.lead_lag_estimators[symbol] = CausalLeadLagEstimator()

        kf = self.filters[symbol]
        ll = self.lead_lag_estimators[symbol]

        # 1. State-space Kalman update
        kf_state = kf.step(spot_price, perp_price, is_us_open, reference_age_seconds)
        
        # 2. Update causal lead-lag
        leadership_score = ll.update(spot_return, perp_return)

        # 3. Compute residuals
        spot_resid_bps = kf_state["spot_residual_bps"]
        perp_resid_bps = kf_state["perp_residual_bps"]
        fair_price = kf_state["fair_price"]

        # Expected round-trip transaction costs
        expected_cost_bps = self.cost_estimator.estimate_round_trip_cost_bps(
            asset_type="spot",
            order_notional=10_000.0,
            bar_turnover=bar_turnover,
            volatility=volatility
        )

        # 4. Uncertainty Envelope (from Kalman estimation error)
        interval_width_bps = kf_state["estimation_std_err"] * 1.96 * 10000.0
        envelope = EdgeEnvelope(
            point_edge=abs(spot_resid_bps),
            lower_edge=max(0.0, abs(spot_resid_bps) - interval_width_bps),
            upper_edge=abs(spot_resid_bps) + interval_width_bps,
            interval_width=interval_width_bps,
            coverage_target=0.90,
            calibration_sample_count=len(ll.spot_returns),
            quality=DataQuality.DERIVED
        )

        direction = SignalDirection.NO_TRADE
        eligible = False
        rejection_reason = None

        # PARALLAX Decision Logic:
        # If Perpetual is leading (leadership_score > 0.15) and Spot is lagging below fair value (spot_resid_bps < -min_edge)
        # -> LONG Laggard Spot!
        # If Perpetual is leading and Spot is overreacting above fair value (spot_resid_bps > min_edge)
        # -> SHORT Overreactor Spot!
        raw_edge_bps = abs(spot_resid_bps)
        net_edge_bps = raw_edge_bps - (expected_cost_bps + self.uncertainty_buffer_bps)

        if raw_edge_bps < (expected_cost_bps + self.uncertainty_buffer_bps):
            rejection_reason = "INSIDE_UNCERTAINTY_OR_COST_ENVELOPE"
        elif abs(leadership_score) < 0.10:
            rejection_reason = "INSUFFICIENT_LEADERSHIP_EVIDENCE"
        else:
            if leadership_score > 0.10 and spot_resid_bps < -self.min_edge_bps:
                direction = SignalDirection.LONG
                eligible = True
            elif leadership_score > 0.10 and spot_resid_bps > self.min_edge_bps:
                direction = SignalDirection.SHORT
                eligible = True
            elif leadership_score < -0.10 and perp_resid_bps < -self.min_edge_bps:
                # Spot leads, perp lags -> trade perp
                direction = SignalDirection.LONG
                eligible = True
            else:
                rejection_reason = "NO_CONVERGENCE_ASYMMETRY"

        return AlphaSignal(
            signal_id=signal_id,
            sleeve=AlphaSleeve.PARALLAX,
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
                "fair_price": fair_price,
                "spot_resid_bps": spot_resid_bps,
                "perp_resid_bps": perp_resid_bps,
                "leadership_score": leadership_score
            }
        )
