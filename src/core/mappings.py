"""All lookup tables and constants for the date calculator.

Ported from date_format_mappings.py — converted to TypedDict for type safety.
"""

from __future__ import annotations

import re
from typing import TypedDict


class DateFormatMapping(TypedDict):
    """Maps a format key to its strftime pattern and regex."""

    name: str
    date_format: str
    regex: str


class TimeFormatMapping(TypedDict):
    """Maps a time format key to its strftime pattern, regex, and preprocessor."""

    name: str
    time_format: str
    regex: str
    pre_process: callable  # (str) -> str


class TimeCalculationEntry(TypedDict):
    """Defines interval parameters for a time unit."""

    interval: str  # 'year', 'month', 'week', 'day', 'hour', 'minute', 'second'
    singular: str
    plural: str
    seconds: int


# ── Date format mappings ──────────────────────────────────────────────

DATE_MAPPINGS: dict[str, DateFormatMapping] = {
    "dd-mm-yy": {"name": "short UK date (-)", "date_format": "%d-%m-%y", "regex": r"\d{2}-\d{2}-\d{2}"},
    "dd-mm-yyyy": {"name": "long UK date (-)", "date_format": "%d-%m-%Y", "regex": r"\d{2}-\d{2}-\d{4}"},
    "dd/mm/yy": {"name": "short UK date (/)", "date_format": "%d/%m/%y", "regex": r"\d{2}/\d{2}/\d{2}"},
    "dd/mm/yyyy": {"name": "long UK date (/)", "date_format": "%d/%m/%Y", "regex": r"\d{2}/\d{2}/\d{4}"},
    "dd.mm.yy": {"name": "short UK date (.)", "date_format": "%d.%m.%y", "regex": r"\d{2}\.\d{2}\.\d{2}"},
    "dd.mm.yyyy": {"name": "long UK date (.)", "date_format": "%d.%m.%Y", "regex": r"\d{2}\.\d{2}\.\d{4}"},
    "mm-dd-yy": {"name": "short US date (-)", "date_format": "%m-%d-%y", "regex": r"\d{2}-\d{2}-\d{2}"},
    "mm-dd-yyyy": {"name": "long US date (-)", "date_format": "%m-%d-%Y", "regex": r"\d{2}-\d{2}-\d{4}"},
    "mm/dd/yy": {"name": "short US date (/)", "date_format": "%m/%d/%y", "regex": r"\d{2}/\d{2}/\d{2}"},
    "mm/dd/yyyy": {"name": "long US date (/)", "date_format": "%m/%d/%Y", "regex": r"\d{2}/\d{2}/\d{4}"},
    "mm.dd.yy": {"name": "short US date (.)", "date_format": "%m.%d.%y", "regex": r"\d{2}\.\d{2}\.\d{2}"},
    "mm.dd.yyyy": {"name": "long US date (.)", "date_format": "%m.%d.%Y", "regex": r"\d{2}\.\d{2}\.\d{4}"},
    "yyyy-mm-dd": {"name": "international (-)", "date_format": "%Y-%m-%d", "regex": r"\d{4}-\d{2}-\d{2}"},
    "yyyymmdd": {"name": "iso", "date_format": "%Y%m%d", "regex": r"\d{8}"},
    "dd mmm yyyy": {"name": "wordy date format", "date_format": "%d %b %Y", "regex": r"\d{2} [a-zA-Z]{3} \d{4}"},
}

# ── Time format mappings ──────────────────────────────────────────────


def _no_process(dt: str) -> str:
    return dt


def _fill_minutes(dt: str) -> str:
    return re.sub(r"(?<![:\d])(?P<num>\d{1,2})(?P<ampm>AM|PM)", r"\g<num>:00\g<ampm>", dt, flags=re.IGNORECASE)


TIME_MAPPINGS: dict[str, TimeFormatMapping] = {
    "24-hour": {
        "name": "24-hour format",
        "time_format": "%H:%M",
        "regex": r"\d{1,2}:\d{2}",
        "pre_process": _no_process,
    },
    "Military": {
        "name": "Military format",
        "time_format": "%H%M",
        "regex": r"\d{4}",
        "pre_process": _no_process,
    },
    "12-hour": {
        "name": "12-hour format",
        "time_format": "%I:%M%p",
        "regex": r"\d{1,2}(:\d{2})?(AM|PM)",
        "pre_process": _fill_minutes,
    },
}

# ── Date-time separator mappings ──────────────────────────────────────
# Calculated at runtime: lambda(date_fmt, time_fmt) -> combined format

DATE_TIME_MAPPINGS: dict[str, dict] = {
    "@": {"date-time-format": lambda date, time: f"{date}@{time}"},
    "T": {"date-time-format": lambda date, time: f"{date}T{time}"},
    "at": {"date-time-format": lambda date, time: f"{date} at {time}"},
    "on": {"date-time-format": lambda date, time: f"{time} on {date}"},
    "arrow": {"date-time-format": lambda date, time: f"DATE ==> {date} TIME ==> {time}"},
}

# ── Defaults ──────────────────────────────────────────────────────────

DEFAULT_DATE_FORMAT = "dd.mm.yy"
DEFAULT_TIME_FORMAT = "24-hour"
DEFAULT_DATE_TIME_FORMAT = "@"

VALID_FORMAT_OPTIONS = ["y", "m", "w", "d", "h", "M", "s"]
VALID_WORD_FORMAT_OPTIONS = ["long"]

TIME_CALCULATION: dict[str, TimeCalculationEntry] = {
    "y": {"interval": "year", "singular": "year", "plural": "years", "seconds": 1 * 60 * 60 * 24 * 7 * 4 * 12},
    "m": {"interval": "month", "singular": "month", "plural": "months", "seconds": 1 * 60 * 60 * 24 * 7 * 4},
    "w": {"interval": "week", "singular": "week", "plural": "weeks", "seconds": 1 * 60 * 60 * 24 * 7},
    "d": {"interval": "day", "singular": "day", "plural": "days", "seconds": 1 * 60 * 60 * 24},
    "h": {"interval": "hour", "singular": "hour", "plural": "hours", "seconds": 1 * 60 * 60},
    "M": {"interval": "minute", "singular": "minute", "plural": "minutes", "seconds": 1 * 60},
    "s": {"interval": "second", "singular": "second", "plural": "seconds", "seconds": 1},
}

DEFAULT_ANNIVERSARIES: dict[str, str] = {
    "christmas": "1900-12-25T00:30:00",
    "alfred": "2010-02-28T00:00:00",
    "leap": "2012-02-29T00:00:00",
    "future": "2072-01-01T00:00:00",
}

DEFAULT_WORKFLOW_SETTINGS: dict[str, object] = {
    "date-format": DEFAULT_DATE_FORMAT,
    "anniversaries": DEFAULT_ANNIVERSARIES,
    "time-format": DEFAULT_TIME_FORMAT,
    "date-time-format": DEFAULT_DATE_TIME_FORMAT,
}

MAX_LOOKAHEAD_ATTEMPTS = 300

# ── Regexes ───────────────────────────────────────────────────────────

WN_FUNCTION_REGEX = re.compile(
    r"wn(\s+(?P<year>\d{4}))?"
    r"(\s+(?P<week_number>\d{1,2}))?"
    r"(\s+(?P<day>mon|tue|wed|thu|fri|sat|sun))?",
    re.IGNORECASE,
)
