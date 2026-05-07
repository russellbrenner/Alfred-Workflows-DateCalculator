"""Date formatter map — output formatting functions.

DATE_FORMATTERS_MAP: maps format keyword to function(datetime) -> str.

Ported from date_formatters.py.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

# Type alias for formatter functions
FormatterFunction = Callable[[datetime], str]

# ── Days of week map ──────────────────────────────────────────────────

DAYS_OF_WEEK: dict[int, str] = {
    1: "MON",
    2: "TUE",
    3: "WED",
    4: "THU",
    5: "FRI",
    6: "SAT",
    7: "SUN",
}


# ── Formatter functions ───────────────────────────────────────────────


def week_number(date_time: datetime) -> str:
    """Return ISO week number (e.g., '23')."""
    raise NotImplementedError("Implementer: date_time.strftime('%V')")


def week_day(date_time: datetime) -> str:
    """Return day of week name (e.g., 'TUE')."""
    raise NotImplementedError("Implementer: lookup DAYS_OF_WEEK[date_time.isoweekday()]")


def week_day_in_isoformat(date_time: datetime) -> str:
    """Return day of week as ISO number (1=Monday, 7=Sunday)."""
    raise NotImplementedError("Implementer: str(date_time.isoweekday())")


def iso_format(date_time: datetime) -> str:
    """Return ISO 8601 format string."""
    raise NotImplementedError("Implementer: date_time.isoformat()")


def zodiac_sign(date_time: datetime) -> str:
    """Return zodiac sign for the given date.

    Uses bisect to find the correct sign based on month/day.
    """
    raise NotImplementedError("Implementer: port from date_formatters.py zodiac_sign")


# ── Formatter map ─────────────────────────────────────────────────────
# Keys matched by the parser; longer keys first (wdi before wd)
# to avoid partial matching issues.

DATE_FORMATTERS_MAP: dict[str, FormatterFunction] = {
    "wdi": week_day_in_isoformat,
    "wn": week_number,
    "wd": week_day,
    "!": week_number,
    "iso": iso_format,
    "sign": zodiac_sign,
}
