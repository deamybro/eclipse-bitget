"""
src/carry/signal.py - CARRY Multi-Leg Basis & Funding Alpha Signal Engine.
Calculates net expected carry after spot/perp fees, slippage, legging penalty,
and corporate action dividend adjustments.
"""

from datetime import datetime
from src.contracts import AlphaSignal, AlphaSleeve, SignalDirection, EdgeEnvelope, DataQuality
from src.carry.basis import BasisCalculator
from src.carry.funding import FundingPersistenceForecaster
from src.execution.costs import CostEstimator


class CarrySignalEngine:
    """Generates delta-hedged funding and basis convergence alpha signals."""

    def __init__(
        self,
        cost_estimator: CostEstimator | None = None,
        min_net_carry_bps: float = 10.0,
        basis_convergence_rate: float = 0.20
    ):
        self.cost_estimator = cost_estimator or CostEstimator()
        self.min_net_carry_bps = min_net_carry_bps
        self.basis_convergence_rate = basis_convergence_rate
        
        self.basis_calc = BasisCalculator(contract_multiplier=0.01)
        self.funding_forecasters: dict[str, FundingPersistenceForecaster] = {}

    def process_bar(
        self,
        symbol: str,
        timestamp_utc: datetime,
        rtoken_price: float,
        perp_price: float,
        funding_rate: float,
        bar_turnover: float,
        volatility: float,
        signal_id: str,
        expected_dividend_cash: float = 0.0
    ) -> AlphaSignal:
        if symbol not in self.funding_forecasters:
            self.funding_forecasters[symbol] = FundingPersistenceForecaster()

        ff = self.funding_forecasters[symbol]
        ewma_fund = ff.update(funding_rate)

        # 1. Log Basis
        log_basis = self.basis_calc.compute_log_basis(rtoken_price, perp_price)
        basis_bps = log_basis * 10000.0

        # 2. Expected Funding over holding window (e.g. 6 periods = 48 hours)
        exp_funding_bps = ff.forecast_cumulative_funding(holding_periods=6) * 10000.0

        # 3. Expected Basis Convergence over window
        exp_basis_convergence_bps = -basis_bps * self.basis_convergence_rate

        # 4. Round-trip transaction costs for PAIR trade (both legs)
        round_trip_cost_bps = self.cost_estimator.estimate_round_trip_cost_bps(
            asset_type="pair",
            order_notional=10_000.0,
            bar_turnover=bar_turnover,
            volatility=volatility
        )

        # 5. Corporate Action Dividend adjustment (in bps)
        div_adjustment_bps = (expected_dividend_cash / rtoken_price) * 10000.0 if rtoken_price > 0 else 0.0

        # 6. Expected Net Carry Calculation:
        # Structure: Long rToken Spot + Short Perp (harvests positive funding + perp premium convergence)
        gross_carry_bps = exp_funding_bps + exp_basis_convergence_bps
        net_carry_bps = gross_carry_bps - round_trip_cost_bps - div_adjustment_bps

        envelope = EdgeEnvelope(
            point_edge=max(0.0, net_carry_bps / 10000.0),
            lower_edge=max(0.0, (net_carry_bps - 5.0) / 10000.0),
            upper_edge=(net_carry_bps + 5.0) / 10000.0,
            interval_width=10.0,
            coverage_target=0.90,
            calibration_sample_count=len(ff.history),
            quality=DataQuality.DERIVED
        )

        direction = SignalDirection.NO_TRADE
        eligible = False
        rejection_reason = None

        if div_adjustment_bps > 0 and (gross_carry_bps - round_trip_cost_bps > 0) and net_carry_bps <= 0:
            rejection_reason = "BLOCKED_BY_DIVIDEND_FIREWALL"
        elif net_carry_bps < self.min_net_carry_bps:
            rejection_reason = "NET_CARRY_BELOW_MINIMUM_HURDLE"
        else:
            # Positive carry trade: Long Spot, Short Perp
            direction = SignalDirection.PAIR
            eligible = True

        return AlphaSignal(
            signal_id=signal_id,
            sleeve=AlphaSleeve.CARRY,
            symbol=symbol,
            timestamp_utc=timestamp_utc,
            direction=direction,
            point_edge=gross_carry_bps / 10000.0,
            edge_envelope=envelope,
            expected_convergence=exp_basis_convergence_bps / 10000.0,
            expected_cost=round_trip_cost_bps / 10000.0,
            expected_net_edge=net_carry_bps / 10000.0,
            eligible=eligible,
            rejection_reason=rejection_reason,
            metadata={
                "log_basis_bps": basis_bps,
                "expected_funding_bps": exp_funding_bps,
                "round_trip_cost_bps": round_trip_cost_bps,
                "div_adjustment_bps": div_adjustment_bps,
                "net_carry_bps": net_carry_bps,
                "hedge_ratio_multiplier": self.basis_calc.contract_multiplier
            }
        )
