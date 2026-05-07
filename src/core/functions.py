"""Date function map — specialised date calculations.

DATE_FUNCTION_MAP: maps keyword strings to functions that return (datetime, format).
EXCLUSION_MAP: maps exclusion keywords to (days_set, rrule_generator).

Ported from date_functions.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from dateutil.rrule import rrule, YEARLY, DAILY

from src.core.settings import Settings


# ── Day-of-week abbreviations ─────────────────────────────────────────

DAYS_OF_WEEK_ABBREVIATIONS: dict[str, str] = {
    "mon": "monday",
    "tue": "tuesday",
    "wed": "wednesday",
    "thu": "thursday",
    "fri": "friday",
    "sat": "saturday",
    "sun": "sunday",
}

# ── Type alias for date functions ────────────────────────────────────

DateFunction = Callable[[Settings], tuple[datetime, str]]

# ── Date function map ─────────────────────────────────────────────────
# Maps keyword → function(settings) -> (datetime, format_str)
# All functions should accept a Settings and return a (datetime, str) tuple.

DATE_FUNCTION_MAP: dict[str, DateFunction] = {
    # Basic: date, today, *, time, &, now, #, yesterday, <, tomorrow, >
    # Weekday navigation: next mon/tue/wed/thu/fri/sat/sun
    # Previous weekday: prev mon/tue/wed/thu/fri/sat/sun
    # Special dates: easter, passover, pancake day, lent, mlk, mom/mum/mutter
    # BST: start bst, end bst
    # Calendar: start year, end year, next month
    #
    # Implementer: port each function from date_functions.py.
    # Each function must:
    #   1. Accept Settings as argument
    #   2. Return (datetime, format_string) tuple
    #   3. Use settings for output format (get_date_format, etc.)
}

# ── Exclusion map ─────────────────────────────────────────────────────
# Maps exclusion keyword → {'days': set[str], 'rule': callable}
# 'days': set of day names to exclude
# 'rule': lambda(start, end) -> dateutil.rrule.rrule object

EXCLUSION_MAP: dict[str, dict] = {
    # Weekday exclusions: weekdays/wkdy, weekends/wknd
    # Individual day exclusions: mondays/mon, tuesdays/tue, etc.
    # Inverse exclusions: all except weekdays/xwkdy, all except mondays/xmon, etc.
    #
    # Implementer: port each entry from date_functions.py EXCLUSION_MAP.
    # Each 'rule' must return an rrule object covering the excluded dates.
}


# ── Format helper functions ───────────────────────────────────────────


def get_date_format(settings: Settings) -> str:
    """Return the strftime date format string from settings."""
    raise NotImplementedError("Implementer: lookup DATE_MAPPINGS[settings.date_format]")


def get_time_format(settings: Settings) -> str:
    """Return the strftime time format string from settings."""
    raise NotImplementedError("Implementer: lookup TIME_MAPPINGS[settings.time_format]")


def get_full_format(settings: Settings) -> str:
    """Return the combined date+time format string from settings."""
    raise NotImplementedError("Implementer: combine date + time format via DATE_TIME_MAPPINGS")


def get_date_format_regex(settings: Settings) -> str:
    """Return the regex pattern for the current date format."""
    raise NotImplementedError("Implementer: lookup DATE_MAPPINGS regex")


def get_time_format_regex(settings: Settings) -> str:
    """Return the regex pattern for the current time format."""
    raise NotImplementedError("Implementer: lookup TIME_MAPPINGS regex")


def get_full_format_regex(settings: Settings) -> str:
    """Return the combined regex pattern for the current date+time format."""
    raise NotImplementedError("Implementer: combine date + time regex via DATE_TIME_MAPPINGS")


def get_time_preprocessor(settings: Settings) -> Callable[[str], str]:
    """Return the time string preprocessor function from settings."""
    raise NotImplementedError("Implementer: lookup TIME_MAPPINGS pre_process")
