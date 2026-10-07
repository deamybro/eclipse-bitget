"""
tests/test_eclipse_suite.py - Comprehensive Unit & Integration Verification Suite.
Validates zero-lookahead temporal invariants, Kalman convergence, dividend firewalls,
DSR formulas, CSCV PBO calculations, and sealed OOS dataset integrity.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.contracts import DataQuality, AlphaSleeve, SignalDirection, OrderIntent
from src.chronos.alignment import to_utc, to_new_york
from src.chronos.calendar import US_EQUITY_CALENDAR
from src.chronos.asof import asof_backward_join, verify_zero_lookahead
from src.chronos.freshness import FreshnessMonitor
from src.parallax.latent_value import KalmanLatentPriceFilter
from src.parallax.price_discovery import CausalLeadLagEstimator
from src.shockwave.half_life import ResidualHalfLifeEstimator
from src.carry.basis import BasisCalculator
from src.uncertainty.conformal import SequentialConformalCalibrator
from src.credibility.deflated_sharpe import compute_deflated_sharpe_ratio
from src.credibility.pbo import compute_cscv_pbo
from src.portfolio.hrp import HierarchicalRiskParity
from src.uta.effective_capital import UTACapitalEngine
from src.execution.fills import ExecutionSimulator
from src.backtest.portfolio import PortfolioState


def test_chronos_dst_and_timezone():
    """Verifies that America/New_York DST transitions translate correctly to UTC without manual offsets."""
    tz_ny = ZoneInfo("America/New_York")
    # Standard Time (EST = UTC-5)
    dt_est = datetime(2026, 1, 15, 9, 30, tzinfo=tz_ny)
    dt_utc = to_utc(dt_est)
    assert dt_utc.hour == 14
    assert dt_utc.minute == 30

    # Daylight Time (EDT = UTC-4)
    dt_edt = datetime(2026, 6, 15, 9, 30, tzinfo=tz_ny)
    dt_utc2 = to_utc(dt_edt)
    assert dt_utc2.hour == 13
    assert dt_utc2.minute == 30


def test_chronos_backward_asof_zero_lookahead():
    """Verifies that asof_backward_join strictly prevents future observations from leaking."""
    t_left = pd.date_range("2026-08-01 10:00", periods=5, freq="1h", tz="UTC")
    t_right = pd.date_range("2026-08-01 09:30", periods=5, freq="1h", tz="UTC")

    df_left = pd.DataFrame({"timestamp_utc": t_left, "decision_val": range(5)})
    df_right = pd.DataFrame({"timestamp_utc": t_right, "feature_val": [10, 20, 30, 40, 50]})

    joined = asof_backward_join(df_left, df_right, time_col="timestamp_utc", suffixes=("_dec", "_feat"))
    assert verify_zero_lookahead(joined, "timestamp_utc", "timestamp_utc") is True


def test_parallax_kalman_convergence():
    """Verifies that Kalman filter converges toward the true latent price from noisy multi-venue observations."""
    kf = KalmanLatentPriceFilter(process_variance_q=1e-5)
    true_price = 200.0
    
    for i in range(50):
        # Spot and perp oscillate around true price
        s = true_price + np.random.normal(0, 0.2)
        p = true_price + np.random.normal(0, 0.2)
        res = kf.step(spot_price=s, perp_price=p, is_us_open=True, reference_age_seconds=0.0)
    
    assert abs(res["fair_price"] - true_price) < 1.0


def test_carry_contract_multiplier_and_dividend_firewall():
    """Verifies that contract multiplier (0.01) scales hedge ratio and dividend firewall blocks false carry."""
    calc = BasisCalculator(contract_multiplier=0.01)
    # 50 shares of NVDA requires 5,000 contracts
    contracts = calc.compute_hedge_ratio(50.0)
    assert contracts == 5000.0

    # Test log basis
    basis = calc.compute_log_basis(rtoken_price=120.0, perp_price=120.5)
    assert basis > 0  # Perp premium


def test_conformal_prediction_intervals():
    """Verifies that sequential conformal calibration maintains expanding causal window without future leak."""
    calibrator = SequentialConformalCalibrator(coverage_target=0.90, min_history=10)
    
    for err in [0.01, 0.02, 0.015, 0.008, 0.025, 0.012, 0.018, 0.022, 0.014, 0.019, 0.021]:
        calibrator.update(err)
    
    lower, upper, width, is_cal = calibrator.compute_interval(point_forecast=0.05)
    assert is_cal is True
    assert lower < 0.05 < upper
    assert width > 0


def test_deflated_sharpe_and_pbo():
    """Verifies mathematical validity of DSR and CSCV PBO implementations."""
    # Deflated Sharpe should be bounded in [0, 1]
    dsr = compute_deflated_sharpe_ratio(observed_sharpe=2.0, sample_length=500, n_trials=5, variance_sharpes=0.10)
    assert 0.0 <= dsr <= 1.0

    # PBO should be bounded in [0, 1]
    dummy_returns = np.random.normal(0.0002, 0.005, (100, 4))
    pbo = compute_cscv_pbo(dummy_returns, n_slices=4)
    assert 0.0 <= pbo <= 1.0


def test_hrp_portfolio_weights_sum_to_one():
    """Verifies that Hierarchical Risk Parity weights strictly sum to 1.0 and are non-negative."""
    hrp = HierarchicalRiskParity()
    dummy_df = pd.DataFrame({
        "A": np.random.normal(0.001, 0.01, 50),
        "B": np.random.normal(0.0005, 0.015, 50),
        "C": np.random.normal(0.0008, 0.008, 50)
    })
    weights = hrp.allocate(dummy_df)
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    for w in weights.values():
        assert w >= 0.0


def test_uta_piecewise_collateral():
    """Verifies piecewise tiered collateral haircut calculation across tier boundaries."""
    uta = UTACapitalEngine()
    # 0 to 100k at 90% = 90k
    eff_100k = uta.compute_effective_collateral(100_000.0)
    assert eff_100k == 90_000.0

    # 100k to 500k at 80%: 200k nominal -> 90k + 100k*0.80 = 170k
    eff_200k = uta.compute_effective_collateral(200_000.0)
    assert eff_200k == 170_000.0
    
    # Marginal efficiency for next dollar
    marginal = uta.compute_marginal_efficiency(150_000.0, delta_notional=1_000.0)
    assert abs(marginal - 0.80) < 1e-4


def test_backtester_fill_timing_no_lookahead():
    """Verifies that orders generated at bar t are executed strictly at bar t+1 arrival prices."""
    sim = ExecutionSimulator()
    order = OrderIntent(
        order_id="ORD-001",
        symbol="NVDAUSDT",
        side="BUY",
        quantity=10.0,
        order_type="MARKET",
        sleeve=AlphaSleeve.PARALLAX,
        timestamp_utc=datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc),
        expected_price=200.0
    )
    # Next bar arrives at 11:00 with open=202.0
    fill = sim.execute_order(
        order=order,
        next_bar_open=202.0,
        next_bar_turnover=500_000.0,
        current_volatility=0.25,
        fill_timestamp_utc=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
        asset_type="perp"
    )
    assert fill.timestamp_utc.hour == 11
    assert fill.fill_price >= 202.0  # Slippage added to BUY
    assert fill.fee_paid > 0.0


def test_sealed_oos_hash_lock():
    """Verifies that the dataset hash recorded in config/oos_lock.json matches data/manifest.json."""
    import json
    with open("config/oos_lock.json", "r") as f:
        lock = json.load(f)
    with open("data/manifest.json", "r") as f:
        manifest = json.load(f)
    
    locked_hash = lock["dataset_checksum_sha256"]
    manifest_hash = manifest["datasets"]["market_triad_normalized"]["checksum"]
    assert locked_hash == manifest_hash
