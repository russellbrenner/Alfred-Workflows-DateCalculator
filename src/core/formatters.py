"""Date formatter map — output formatting functions.

DATE_FORMATTERS_MAP: maps format keyword to function(datetime) -> str.

Ported from date_formatters.py.
"""

from __future__ import annotations

from bisect import bisect
from collections.abc import Callable
from datetime import datetime

FormatterFunction = Callable[[datetime], str]

DAYS_OF_WEEK: dict[int, str] = {
    1: "MON",
    2: "TUE",
    3: "WED",
    4: "THU",
    5: "FRI",
    6: "SAT",
    7: "SUN",
}


def week_number(date_time: datetime) -> str:
    """Return ISO week number (e.g., '23')."""
    return date_time.strftime("%V")


def week_day(date_time: datetime) -> str:
    """Return day of week name (e.g., 'TUE')."""
    return DAYS_OF_WEEK[date_time.isoweekday()]


def week_day_in_isoformat(date_time: datetime) -> str:
    """Return day of week as ISO number (1=Monday, 7=Sunday)."""
    return str(date_time.isoweekday())


def iso_format(date_time: datetime) -> str:
    """Return ISO 8601 format string."""
    return date_time.isoformat()


def zodiac_sign(date_time: datetime) -> str:
    """Return zodiac sign for the given date using the legacy bisect table."""
    signs = [
        (1, 20, "Capricorn"),
        (2, 18, "Aquarius"),
        (3, 20, "Pisces"),
        (4, 20, "Aries"),
        (5, 21, "Taurus"),
        (6, 21, "Gemini"),
        (7, 22, "Cancer"),
        (8, 23, "Leo"),
        (9, 23, "Virgo"),
        (10, 23, "Libra"),
        (11, 22, "Scorpio"),
        (12, 22, "Sagittarius"),
        (12, 31, "Capricorn"),
    ]
    return signs[bisect(signs, (date_time.month, date_time.day))][2]


DATE_FORMATTERS_MAP: dict[str, FormatterFunction] = {
    "wdi": week_day_in_isoformat,
    "wn": week_number,
    "wd": week_day,
    "!": week_number,
    "iso": iso_format,
    "sign": zodiac_sign,
}
