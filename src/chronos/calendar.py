"""
src/chronos/calendar.py - NYSE / NASDAQ Exchange Holiday & Calendar System.
Maintains official market closure dates, early closing sessions (13:00 ET),
and accurate business calendar logic without third-party dependencies.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Set

TZ_ET = ZoneInfo("America/New_York")


def get_easter(year: int) -> date:
    """Computes Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_good_friday(year: int) -> date:
    """Returns Good Friday (2 days before Easter Sunday)."""
    from datetime import timedelta
    return get_easter(year) - timedelta(days=2)


def get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """Finds the nth occurrence of a weekday in a given month (0=Monday)."""
    count = 0
    for day in range(1, 32):
        try:
            d = date(year, month, day)
            if d.weekday() == weekday:
                count += 1
                if count == n:
                    return d
        except ValueError:
            break
    raise ValueError(f"Could not find {n}th weekday {weekday} in month {month}, {year}")


def get_last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """Finds the last occurrence of a weekday in a given month."""
    for day in range(31, 0, -1):
        try:
            d = date(year, month, day)
            if d.weekday() == weekday:
                return d
        except ValueError:
            continue
    raise ValueError(f"Could not find last weekday {weekday} in month {month}, {year}")


class ExchangeCalendar:
    """Official NYSE / NASDAQ holiday and half-day schedule provider."""

    def __init__(self, years=(2024, 2025, 2026, 2027)):
        self.holidays: Set[date] = set()
        self.half_days: Set[date] = set()
        self._build_schedule(years)

    def _build_schedule(self, years):
        for y in years:
            # 1. New Year's Day (observed)
            nyd = date(y, 1, 1)
            if nyd.weekday() == 6:  # Sunday -> Monday
                self.holidays.add(date(y, 1, 2))
            else:
                self.holidays.add(nyd)

            # 2. Martin Luther King Jr. Day (3rd Monday in Jan)
            self.holidays.add(get_nth_weekday_of_month(y, 1, 0, 3))

            # 3. Washington's Birthday / Presidents' Day (3rd Monday in Feb)
            self.holidays.add(get_nth_weekday_of_month(y, 2, 0, 3))

            # 4. Good Friday
            self.holidays.add(get_good_friday(y))

            # 5. Memorial Day (last Monday in May)
            self.holidays.add(get_last_weekday_of_month(y, 5, 0))

            # 6. Juneteenth National Independence Day (June 19, observed)
            june19 = date(y, 6, 19)
            if june19.weekday() == 5:
                self.holidays.add(date(y, 6, 18))
            elif june19.weekday() == 6:
                self.holidays.add(date(y, 6, 20))
            else:
                self.holidays.add(june19)

            # 7. Independence Day (July 4, observed)
            july4 = date(y, 7, 4)
            if july4.weekday() == 5:
                self.holidays.add(date(y, 7, 3))
            elif july4.weekday() == 6:
                self.holidays.add(date(y, 7, 5))
            else:
                self.holidays.add(july4)
            # July 3rd is early close (13:00 ET) if July 4 is weekday
            if july4.weekday() in (1, 2, 3, 4):
                self.half_days.add(date(y, 7, 3))

            # 8. Labor Day (1st Monday in Sept)
            self.holidays.add(get_nth_weekday_of_month(y, 9, 0, 1))

            # 9. Thanksgiving Day (4th Thursday in Nov)
            thanksgiving = get_nth_weekday_of_month(y, 11, 3, 4)
            self.holidays.add(thanksgiving)
            # Day after Thanksgiving (Black Friday) is half day
            from datetime import timedelta
            self.half_days.add(thanksgiving + timedelta(days=1))

            # 10. Christmas Day (Dec 25, observed)
            xmas = date(y, 12, 25)
            if xmas.weekday() == 5:
                self.holidays.add(date(y, 12, 24))
            elif xmas.weekday() == 6:
                self.holidays.add(date(y, 12, 26))
            else:
                self.holidays.add(xmas)
                # Christmas Eve early close
                if xmas.weekday() in (1, 2, 3, 4):
                    self.half_days.add(date(y, 12, 24))

    def is_holiday(self, dt: datetime) -> bool:
        dt_et = dt.astimezone(TZ_ET) if dt.tzinfo else dt
        return dt_et.date() in self.holidays

    def is_half_day(self, dt: datetime) -> bool:
        dt_et = dt.astimezone(TZ_ET) if dt.tzinfo else dt
        return dt_et.date() in self.half_days

    def is_trading_day(self, dt: datetime) -> bool:
        dt_et = dt.astimezone(TZ_ET) if dt.tzinfo else dt
        if dt_et.weekday() in (5, 6):
            return False
        return dt_et.date() not in self.holidays


# Global default exchange calendar instance
US_EQUITY_CALENDAR = ExchangeCalendar()
