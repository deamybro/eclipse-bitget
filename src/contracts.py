"""
ECLIPSE Core Data Contracts & Domain Models
Strictly typed, immutable Pydantic models for zero-lookahead financial engineering.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DataQuality(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    MODELLED = "modelled"
    PROXY = "proxy"
    REPLAY = "replay"
    UNAVAILABLE = "unavailable"


class MarketSession(str, Enum):
    US_REGULAR = "us_regular"
    US_PRE = "us_pre"
    US_POST = "us_post"
    WEEKEND = "weekend"
    OVERNIGHT = "overnight"
    CLOSED = "closed"


class CapitalStatus(str, Enum):
    FULL_RISK = "FULL_RISK"
    REDUCED_RISK = "REDUCED_RISK"
    WATCH = "WATCH"
    DISABLED = "DISABLED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"
    PAIR = "PAIR"
    NO_TRADE = "NO_TRADE"


class AlphaSleeve(str, Enum):
    PARALLAX = "PARALLAX"
    SHOCKWAVE = "SHOCKWAVE"
    CARRY = "CARRY"


class CorporateActionType(str, Enum):
    CASH_DIVIDEND = "cash_dividend"
    STOCK_SPLIT = "stock_split"
    REVERSE_SPLIT = "reverse_split"
    SPECIAL_DIVIDEND = "special_dividend"
    STOCK_DIVIDEND = "stock_dividend"


class MarketBar(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    timestamp_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None
    source: str
    source_timestamp: Optional[datetime] = None
    ingestion_timestamp: datetime
    quality: DataQuality = DataQuality.OBSERVED
    session: Optional[MarketSession] = None


class MarketQuote(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    timestamp_utc: datetime
    bid_price: float
    bid_qty: float
    ask_price: float
    ask_qty: float
    spread_bps: float
    source: str
    quality: DataQuality = DataQuality.OBSERVED


class FundingObservation(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    funding_rate: float
    funding_time_utc: datetime
    settlement_period_hours: int = 8
    source: str = "bitget_perpetuals"
    quality: DataQuality = DataQuality.OBSERVED


class CorporateAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    action_type: CorporateActionType
    effective_date_utc: datetime
    announcement_time_utc: datetime
    known_at_utc: datetime
    adjustment_factor: float = 1.0
    cash_amount: float = 0.0
    quality: DataQuality = DataQuality.OBSERVED


class CollateralTier(BaseModel):
    model_config = ConfigDict(frozen=True)

    asset: str
    notional_min: float
    notional_max: float
    ratio: float
    effective_from_utc: datetime
    effective_to_utc: Optional[datetime] = None
    source: str
    quality: DataQuality = DataQuality.OBSERVED


class SessionState(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_utc: datetime
    session: MarketSession
    is_us_open: bool
    is_rtoken_open: bool
    underlying_open: bool
    reference_age_seconds: float = 0.0


class AlignedSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_utc: datetime
    underlying: str
    rtoken_symbol: str
    stock_perp_symbol: Optional[str] = None
    native_symbol: Optional[str] = None
    
    rtoken_price: float
    stock_perp_price: Optional[float] = None
    native_price: Optional[float] = None
    
    log_basis: Optional[float] = None
    session_state: SessionState
    quality: DataQuality = DataQuality.DERIVED


class EdgeEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    point_edge: float
    lower_edge: float
    upper_edge: float
    interval_width: float
    coverage_target: float = 0.90
    calibration_sample_count: int
    quality: DataQuality = DataQuality.DERIVED


class AlphaSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal_id: str
    sleeve: AlphaSleeve
    symbol: str
    timestamp_utc: datetime
    direction: SignalDirection
    point_edge: float
    edge_envelope: EdgeEnvelope
    expected_convergence: float
    expected_cost: float
    expected_net_edge: float
    eligible: bool
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RegimeState(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_utc: datetime
    regime_id: int
    regime_name: str
    probabilities: Dict[str, float]
    structural_break_detected: bool
    break_metric: float = 0.0
    quality: DataQuality = DataQuality.DERIVED


class CredibilityReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    sleeve: AlphaSleeve
    in_sample_sharpe: float
    out_of_sample_sharpe: float
    oos_is_ratio: float
    sortino: float
    max_drawdown: float
    rolling_sharpe_stability: float
    deflated_sharpe: float
    pbo: float
    parameter_stability: float
    cost_survival_ratio: float
    signal_ic: float
    recent_decay_status: str
    trade_count: int
    sample_adequate: bool
    capital_status: CapitalStatus


class SleeveAllocation(BaseModel):
    model_config = ConfigDict(frozen=True)

    sleeve: AlphaSleeve
    target_weight: float
    effective_weight: float
    status: CapitalStatus
    regime_fit: float
    shadow_cost_penalty: float = 0.0


class PortfolioAllocation(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp_utc: datetime
    allocations: Dict[str, float]
    cash_weight: float
    gross_exposure: float
    net_exposure: float
    rebalance_executed: bool
    volatility_target_scalar: float = 1.0
    drawdown_throttle_scalar: float = 1.0


class OrderIntent(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: str
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    order_type: str  # MARKET, LIMIT
    sleeve: AlphaSleeve
    timestamp_utc: datetime
    expected_price: float
    limit_price: Optional[float] = None
    notes: Optional[str] = None


class BacktestFill(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: str
    fill_id: str
    symbol: str
    side: str
    fill_price: float
    fill_qty: float
    fee_paid: float
    slippage_bps: float
    timestamp_utc: datetime


class TradeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    trade_id: str
    sleeve: AlphaSleeve
    symbol: str
    entry_time_utc: datetime
    exit_time_utc: Optional[datetime] = None
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    pnl: float = 0.0
    fees_paid: float = 0.0
    funding_paid_or_received: float = 0.0
    holding_period_seconds: float = 0.0


class ExperimentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    strategy: str
    parameter_hash: str
    parameters: Dict[str, Any]
    feature_hash: str
    training_period: str
    validation_period: str
    oos_period: str
    metrics: Dict[str, float]
    created_at_utc: datetime
    parent_experiment: Optional[str] = None
