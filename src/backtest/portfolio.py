"""
src/backtest/portfolio.py - Multi-Asset Position & Capital Accounting Engine.
Manages cash, margin, multi-leg positions, unrealized PnL, and exposure metrics.
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from src.contracts import BacktestFill, AlphaSleeve


class PositionLeg(BaseModel):
    symbol: str
    asset_type: str  # spot or perp
    quantity: float = 0.0
    entry_price: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    fees_paid: float = 0.0
    funding_paid_or_received: float = 0.0
    sleeve: AlphaSleeve


class PortfolioState:
    """Maintains institutional portfolio cash and margin accounts."""

    def __init__(self, initial_cash: float = 100_000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, PositionLeg] = {}
        self.equity_history: List[dict] = []
        self.trade_history: List[dict] = []

    @property
    def total_unrealized_pnl(self) -> float:
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def total_equity(self) -> float:
        spot_market_val = sum(pos.quantity * pos.current_price for pos in self.positions.values() if pos.asset_type == "spot")
        perp_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values() if pos.asset_type != "spot")
        return self.cash + spot_market_val + perp_unrealized

    @property
    def gross_notional(self) -> float:
        return sum(abs(pos.quantity * pos.current_price) for pos in self.positions.values())

    @property
    def net_notional(self) -> float:
        return sum(pos.quantity * pos.current_price for pos in self.positions.values())

    def update_market_prices(self, price_map: Dict[str, float], timestamp_utc: datetime):
        """Marks all open positions to market."""
        for sym, pos in self.positions.items():
            if sym in price_map:
                p = price_map[sym]
                pos.current_price = p
                if pos.asset_type == "spot":
                    pos.unrealized_pnl = pos.quantity * (p - pos.entry_price)
                else:  # perp (can be short)
                    pos.unrealized_pnl = pos.quantity * (p - pos.entry_price)

        self.equity_history.append({
            "timestamp_utc": timestamp_utc,
            "cash": self.cash,
            "total_equity": self.total_equity,
            "gross_notional": self.gross_notional,
            "net_notional": self.net_notional,
            "cash_weight": self.cash / max(1.0, self.total_equity)
        })

    def process_fill(self, fill: BacktestFill, sleeve: AlphaSleeve, asset_type: str = "perp"):
        """Updates positions and cash balances upon trade fill."""
        sym = fill.symbol
        signed_qty = fill.fill_qty if fill.side.upper() == "BUY" else -fill.fill_qty
        
        # Deduct transaction fee
        self.cash -= fill.fee_paid

        if sym not in self.positions:
            self.positions[sym] = PositionLeg(
                symbol=sym,
                asset_type=asset_type,
                quantity=signed_qty,
                entry_price=fill.fill_price,
                current_price=fill.fill_price,
                fees_paid=fill.fee_paid,
                sleeve=sleeve
            )
            if asset_type == "spot":
                self.cash -= signed_qty * fill.fill_price
        else:
            pos = self.positions[sym]
            old_qty = pos.quantity
            new_qty = old_qty + signed_qty

            if old_qty * signed_qty > 0:
                # Adding to existing position: weighted average entry price
                new_cost = (old_qty * pos.entry_price) + (signed_qty * fill.fill_price)
                pos.entry_price = new_cost / new_qty
                pos.quantity = new_qty
                pos.fees_paid += fill.fee_paid
                if asset_type == "spot":
                    self.cash -= signed_qty * fill.fill_price
            else:
                # Reducing or closing position
                closed_qty = min(abs(old_qty), abs(signed_qty))
                realized = closed_qty * (fill.fill_price - pos.entry_price) if old_qty > 0 else closed_qty * (pos.entry_price - fill.fill_price)
                pos.realized_pnl += realized
                pos.fees_paid += fill.fee_paid
                
                if asset_type == "spot":
                    self.cash += closed_qty * fill.fill_price
                else:
                    self.cash += realized

                pos.quantity = new_qty
                if abs(new_qty) < 1e-8:
                    pos.quantity = 0.0
                    pos.unrealized_pnl = 0.0
                elif (old_qty > 0 and new_qty < 0) or (old_qty < 0 and new_qty > 0):
                    # Position flipped sides! New residual position has entry price of current fill
                    pos.entry_price = fill.fill_price

        self.trade_history.append({
            "order_id": fill.order_id,
            "fill_id": fill.fill_id,
            "symbol": sym,
            "side": fill.side,
            "quantity": fill.fill_qty,
            "fill_price": fill.fill_price,
            "fee": fill.fee_paid,
            "slippage_bps": fill.slippage_bps,
            "timestamp_utc": fill.timestamp_utc,
            "sleeve": sleeve.value
        })

    def apply_funding(self, symbol: str, funding_rate: float, timestamp_utc: datetime):
        """
        Settles 8-hour funding cash flows:
        Cash Flow = -1 * Position Quantity * Mark Price * Funding Rate
        (Long pays short when funding_rate > 0)
        """
        if symbol in self.positions:
            pos = self.positions[symbol]
            if pos.quantity != 0.0 and pos.asset_type == "perp":
                notional = pos.quantity * pos.current_price
                # Long pays short when funding_rate > 0
                cash_delta = -notional * funding_rate
                self.cash += cash_delta
                pos.funding_paid_or_received += cash_delta
