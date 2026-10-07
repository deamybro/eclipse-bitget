"""
src/chronos/asof.py - Strict Backward As-Of Join Engine.
Enforces zero-lookahead information boundary: at decision timestamp t,
only records with timestamp <= t may be attached.
"""

from typing import List, Optional
import pandas as pd
from datetime import datetime


def asof_backward_join(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    time_col: str = "timestamp_utc",
    by_col: Optional[str] = None,
    tolerance_seconds: Optional[float] = None,
    suffixes: tuple = ("", "_right")
) -> pd.DataFrame:
    """
    Performs a strict backward as-of join between two DataFrames.
    Ensures left_df[time_col] >= right_df[time_col].
    Guarantees no future information leaks into historical decision timestamps.
    """
    left = left_df.copy()
    right = right_df.copy()

    # Ensure time columns are datetime and sorted
    left[time_col] = pd.to_datetime(left[time_col], utc=True)
    right[time_col] = pd.to_datetime(right[time_col], utc=True)

    left = left.sort_values(time_col)
    right = right.sort_values(time_col)

    tolerance = pd.Timedelta(seconds=tolerance_seconds) if tolerance_seconds else None

    joined = pd.merge_asof(
        left,
        right,
        on=time_col,
        by=by_col,
        direction="backward",
        tolerance=tolerance,
        suffixes=suffixes
    )

    return joined


def verify_zero_lookahead(
    df: pd.DataFrame,
    decision_time_col: str,
    feature_time_col: str
) -> bool:
    """
    Unit-test verification helper: confirms that no feature timestamp
    is strictly greater than the decision timestamp.
    """
    violations = df[df[feature_time_col] > df[decision_time_col]]
    if not violations.empty:
        raise ValueError(
            f"LOOKAHEAD VIOLATION DETECTED! {len(violations)} rows have feature_time > decision_time."
        )
    return True
