"""
src/chronos/sessions.py - Market Session Classification & Demarcation.
Provides precise session identification for U.S. Equities (NYSE/NASDAQ) and 24/7 Bitget markets.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo
from src.contracts import MarketSession, SessionState

TZ_ET = ZoneInfo("America/New_York")
TZ_UTC = ZoneInfo("UTC")

# Standard U.S. Equity Trading Hours (Eastern Time)
PRE_MARKET_START = time(4, 0)
REGULAR_MARKET_OPEN = time(9, 30)
REGULAR_MARKET_CLOSE = time(16, 0)
POST_MARKET_END = time(20, 0)


def get_market_session(dt_utc: datetime, is_holiday: bool = False, is_half_day: bool = False) -> MarketSession:
    """
    Determines market session based on event timestamp in UTC.
    Converts strictly to America/New_York taking DST into account.
    """
    dt_et = dt_utc.astimezone(TZ_ET)
    weekday = dt_et.weekday()  # 0=Monday, ..., 4=Friday, 5=Saturday, 6=Sunday

    # Weekend check
    if weekday in (5, 6):
        return MarketSession.WEEKEND

    # Holiday check
    if is_holiday:
        return MarketSession.CLOSED

    t = dt_et.time()

    regular_close = time(13, 0) if is_half_day else REGULAR_MARKET_CLOSE

    if t < PRE_MARKET_START:
        return MarketSession.OVERNIGHT
    elif PRE_MARKET_START <= t < REGULAR_MARKET_OPEN:
        return MarketSession.US_PRE
    elif REGULAR_MARKET_OPEN <= t < regular_close:
        return MarketSession.US_REGULAR
    elif regular_close <= t < POST_MARKET_END:
        return MarketSession.US_POST
    else:
        return MarketSession.OVERNIGHT


def evaluate_session_state(
    dt_utc: datetime,
    last_underlying_update_utc: datetime,
    is_holiday: bool = False,
    is_half_day: bool = False
) -> SessionState:
    """
    Computes full temporal SessionState, including underlying market status
    and reference price age (staleness) in seconds.
    """
    session = get_market_session(dt_utc, is_holiday, is_half_day)
    is_us_regular = (session == MarketSession.US_REGULAR)
    
    # rTokens trade 24/7 on Bitget spot
    is_rtoken_open = True
    
    # Underlying stock is considered actively open during regular hours
    underlying_open = is_us_regular
    
    age_seconds = max(0.0, (dt_utc - last_underlying_update_utc).total_seconds())

    return SessionState(
        timestamp_utc=dt_utc,
        session=session,
        is_us_open=is_us_regular,
        is_rtoken_open=is_rtoken_open,
        underlying_open=underlying_open,
        reference_age_seconds=age_seconds
    )
