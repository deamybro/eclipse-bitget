"""
src/chronos/alignment.py - Timestamp Alignment & Timezone Integrity Engine.
Guarantees all internal temporal representations are strictly UTC-aware,
free from manual hour offsets, and synchronized across multi-venue feeds.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Union

TZ_UTC = ZoneInfo("UTC")
TZ_ET = ZoneInfo("America/New_York")


def to_utc(val: Union[int, float, str, datetime]) -> datetime:
    """
    Converts various timestamp formats (epoch ms, epoch sec, ISO string, datetime)
    into a timezone-aware UTC datetime.
    """
    if isinstance(val, (int, float)):
        # Epoch timestamp: detect whether in seconds or milliseconds
        if val > 1e11:  # Milliseconds
            return datetime.fromtimestamp(val / 1000.0, tz=TZ_UTC)
        else:  # Seconds
            return datetime.fromtimestamp(val, tz=TZ_UTC)
    elif isinstance(val, str):
        # Parse ISO string or numeric string
        try:
            numeric_val = float(val)
            return to_utc(numeric_val)
        except ValueError:
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=TZ_UTC)
            return dt.astimezone(TZ_UTC)
    elif isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=TZ_UTC)
        return val.astimezone(TZ_UTC)
    else:
        raise TypeError(f"Unsupported timestamp type: {type(val)} ({val})")


def to_new_york(dt: datetime) -> datetime:
    """Converts any timezone-aware datetime to America/New_York."""
    utc_dt = to_utc(dt)
    return utc_dt.astimezone(TZ_ET)


def format_session_timestamp(dt: datetime) -> dict:
    """Returns canonical dual-timezone representations for audit ledgers."""
    utc_dt = to_utc(dt)
    et_dt = utc_dt.astimezone(TZ_ET)
    return {
        "event_time_utc": utc_dt.isoformat(),
        "event_time_et": et_dt.isoformat(),
        "epoch_ms": int(utc_dt.timestamp() * 1000),
        "is_dst": bool(et_dt.dst())
    }
