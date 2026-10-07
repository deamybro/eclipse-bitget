"""
src/execution/fills.py - Strict Next-Bar Order Fill Execution Engine.
Prevents same-bar lookahead leakage by strictly executing bar t signals
at bar t+1 arrival/open prices, adjusted for fees and impact.
"""

from datetime import datetime
from src.contracts import OrderIntent, BacktestFill, AlphaSleeve
from src.execution.fees import FeeModel
from src.execution.slippage import MarketImpactModel


class ExecutionSimulator:
    """Simulates realistic trade fills with strict timing rules and cost penalties."""

    def __init__(
        self,
        fee_model: FeeModel | None = None,
        impact_model: MarketImpactModel | None = None,
        stress_multiplier: float = 1.0
    ):
        self.fee_model = fee_model or FeeModel()
        self.impact_model = impact_model or MarketImpactModel()
        self.stress_multiplier = stress_multiplier
        self._fill_counter = 0

    def execute_order(
        self,
        order: OrderIntent,
        next_bar_open: float,
        next_bar_turnover: float,
        current_volatility: float,
        fill_timestamp_utc: datetime,
        asset_type: str = "perp"
    ) -> BacktestFill:
        """
        Executes order strictly at next_bar_open, applying slippage and fees.
        """
        self._fill_counter += 1
        fill_id = f"FILL-{self._fill_counter:06d}"
        
        notional = order.quantity * next_bar_open
        
        # Apply slippage
        exec_price, slip_bps = self.impact_model.apply_slippage(
            base_price=next_bar_open,
            side=order.side,
            order_notional=notional,
            bar_turnover=next_bar_turnover,
            volatility=current_volatility,
            stress_multiplier=self.stress_multiplier
        )
        
        # Apply fees
        fee = self.fee_model.compute_fee(
            notional=order.quantity * exec_price,
            asset_type="spot" if asset_type == "spot" else "perp",
            order_style="taker"
        )

        return BacktestFill(
            order_id=order.order_id,
            fill_id=fill_id,
            symbol=order.symbol,
            side=order.side,
            fill_price=exec_price,
            fill_qty=order.quantity,
            fee_paid=fee,
            slippage_bps=slip_bps,
            timestamp_utc=fill_timestamp_utc
        )
