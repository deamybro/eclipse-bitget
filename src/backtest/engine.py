"""
src/backtest/engine.py - Event-Driven Backtesting Core Engine.
Implements bar-by-bar chronological execution, zero same-bar fill leakage,
periodic funding settlement, multi-leg order tracking, and equity accounting.
"""

from typing import List, Dict, Callable, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np

from src.contracts import OrderIntent, BacktestFill, AlphaSleeve
from src.backtest.portfolio import PortfolioState
from src.execution.fills import ExecutionSimulator
from src.execution.fees import FeeModel
from src.execution.slippage import MarketImpactModel


class EventDrivenBacktester:
    """Discrete bar-by-bar institutional multi-asset backtester."""

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        fee_model: Optional[FeeModel] = None,
        impact_model: Optional[MarketImpactModel] = None,
        stress_multiplier: float = 1.0
    ):
        self.portfolio = PortfolioState(initial_cash=initial_cash)
        self.execution_sim = ExecutionSimulator(
            fee_model=fee_model,
            impact_model=impact_model,
            stress_multiplier=stress_multiplier
        )
        self.pending_orders: List[OrderIntent] = []
        self.fills: List[BacktestFill] = []

    def run(
        self,
        market_df: pd.DataFrame,
        strategy_callback: Callable[[pd.Series, PortfolioState], List[OrderIntent]]
    ) -> Dict[str, Any]:
        """
        Runs event-driven backtest over market_df.
        market_df must be sorted chronologically by timestamp_utc.
        """
        timestamps = market_df["timestamp_utc"].drop_duplicates().sort_values().tolist()
        order_counter = 0

        for idx, ts in enumerate(timestamps):
            current_bars = market_df[market_df["timestamp_utc"] == ts]
            price_map = {}
            turnover_map = {}
            vol_map = {}

            for _, row in current_bars.iterrows():
                sym = row["perp_symbol"]
                price_map[sym] = row["perp_close"]
                turnover_map[sym] = row.get("perp_volume", 1000.0) * row["perp_close"]
                vol_map[sym] = row.get("rtoken_vol_24h", 0.30)
                
                # Also track spot rToken prices
                spot_sym = row["rtoken_symbol"]
                price_map[spot_sym] = row["rtoken_close"]
                turnover_map[spot_sym] = row.get("rtoken_volume", 1000.0) * row["rtoken_close"]
                vol_map[spot_sym] = row.get("rtoken_vol_24h", 0.30)

            # 1. EXECUTE PENDING ORDERS from bar t-1 at bar t arrival price (Open)
            if self.pending_orders:
                orders_to_fill = list(self.pending_orders)
                self.pending_orders = []
                for order in orders_to_fill:
                    sym = order.symbol
                    # Determine arrival price (open if available, else close)
                    bar_row = current_bars[
                        (current_bars["perp_symbol"] == sym) | (current_bars["rtoken_symbol"] == sym)
                    ]
                    if not bar_row.empty:
                        r = bar_row.iloc[0]
                        is_spot = (sym == r["rtoken_symbol"])
                        arrival_price = r["rtoken_open"] if is_spot else r["perp_open"]
                        turnover = turnover_map.get(sym, 100_000.0)
                        vol = vol_map.get(sym, 0.30)
                        
                        fill = self.execution_sim.execute_order(
                            order=order,
                            next_bar_open=arrival_price,
                            next_bar_turnover=turnover,
                            current_volatility=vol,
                            fill_timestamp_utc=ts,
                            asset_type="spot" if is_spot else "perp"
                        )
                        self.fills.append(fill)
                        self.portfolio.process_fill(
                            fill=fill,
                            sleeve=order.sleeve,
                            asset_type="spot" if is_spot else "perp"
                        )

            # 2. FUNDING RATE SETTLEMENT (8-hour cadence: 00:00, 08:00, 16:00 UTC)
            if ts.hour in (0, 8, 16) and ts.minute == 0:
                for _, row in current_bars.iterrows():
                    sym = row["perp_symbol"]
                    rate = row.get("funding_rate", 0.0)
                    if rate != 0.0:
                        self.portfolio.apply_funding(sym, rate, ts)

            # 3. MARK TO MARKET at bar close
            self.portfolio.update_market_prices(price_map, ts)

            # 4. STRATEGY EVALUATION at bar t close -> Generates pending orders for bar t+1
            for _, row in current_bars.iterrows():
                new_orders = strategy_callback(row, self.portfolio)
                if new_orders:
                    for no in new_orders:
                        order_counter += 1
                        # Ensure unique order id
                        o = OrderIntent(
                            order_id=f"ORD-{order_counter:06d}",
                            symbol=no.symbol,
                            side=no.side,
                            quantity=no.quantity,
                            order_type=no.order_type,
                            sleeve=no.sleeve,
                            timestamp_utc=ts,
                            expected_price=no.expected_price,
                            notes=no.notes
                        )
                        self.pending_orders.append(o)

        equity_df = pd.DataFrame(self.portfolio.equity_history)
        trades_df = pd.DataFrame(self.portfolio.trade_history)

        return {
            "initial_cash": self.portfolio.initial_cash,
            "final_equity": self.portfolio.total_equity,
            "net_pnl": self.portfolio.total_equity - self.portfolio.initial_cash,
            "equity_curve": equity_df,
            "trades": trades_df,
            "fills_count": len(self.fills)
        }
