"""Date arithmetic engine — pure functions for computation.

All functions accept an optional `now_fn` parameter for testability
(injectable time). Default is `datetime.datetime.now`.

Ported from date_calculator.py, utils.py, and date_functions.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from collections.abc import Callable

from src.core.parser import (
    TimespanCommand,
    SubtractionCommand,
    Operand,
    TimeSpan,
    ExclusionCommands,
)
from src.core.settings import Settings


# ── Exceptions ────────────────────────────────────────────────────────


class FormatError(Exception):
    """Raised when a format option has repeated characters (invalid)."""


class IncompatibleFunctionError(Exception):
    """Raised when exclusions are used with formatting (not supported)."""


class UnknownExclusionTypeError(Exception):
    """Raised when an unrecognized exclusion type is encountered."""


class ExclusionTooFarAheadError(Exception):
    """Raised when exclusion lookahead exceeds MAX_LOOKAHEAD_ATTEMPTS."""


class ExclusionNoDaysFoundError(Exception):
    """Raised when all days in the week are excluded."""


# ── Main dispatcher ──────────────────────────────────────────────────


def execute_command(
    command: TimespanCommand | SubtractionCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Execute a parsed command and return the result string.

    Routes to the appropriate handler based on command type.

    Args:
        command: Parsed command (TimespanCommand or SubtractionCommand).
        settings: Workflow settings.
        now_fn: Optional time injection function for testing.

    Returns:
        Result string for display in Alfred.
    """
    raise NotImplementedError("Implementer: dispatch based on command type")


# ── Timespan handling ─────────────────────────────────────────────────


def do_timespans(
    command: TimespanCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Process a timespan command (e.g., 'now + 6d').

    Steps:
    1. Convert dateTime string to datetime.
    2. Apply all operands (delta arithmetic).
    3. Apply exclusions if present.
    4. Format output.

    Returns the formatted date/time string.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py do_timespans")


# ── Subtraction handling ──────────────────────────────────────────────


def do_subtraction(
    command: SubtractionCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Process a subtraction command (e.g., '25.12.14 - 18.01.14').

    Steps:
    1. Convert both dateTime strings to datetimes.
    2. Apply any operands on either side.
    3. Calculate normalised days/difference.
    4. Format according to command.format option.

    Returns the formatted difference string.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py do_subtraction")


# ── Format handling ───────────────────────────────────────────────────


def do_formats(
    command: TimespanCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Apply a format function to a datetime string.

    Looks up command.date_format in DATE_FORMATTERS_MAP and applies it.

    Returns the formatted result string.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py do_formats")


# ── Delta arithmetic ──────────────────────────────────────────────────


def delta_arithmetic(
    date_time: datetime,
    operand_list: list[Operand],
) -> datetime:
    """Apply a list of operands to a datetime via relativedelta.

    Each operand adds or subtracts its TimeSpan components.

    Args:
        date_time: Starting datetime.
        operand_list: List of Operand objects with operator and time spans.

    Returns:
        Resulting datetime after all operations.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py delta_arithmetic")


# ── Exclusion handling ────────────────────────────────────────────────


def exclusion_check(
    original_date_time: datetime,
    date_time: datetime,
    command: TimespanCommand,
    settings: Settings,
) -> datetime:
    """Apply exclusion rules if present on the command.

    If the command has no exclusions, returns date_time unchanged.

    Otherwise, calculates how many days are excluded between the
    original and target dates, and adjusts the target date forward.

    Raises:
        ExclusionNoDaysFoundError: If all 7 days are excluded.
        ExclusionTooFarAheadError: If lookahead exceeds limit.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py exclusion_check")


def build_exclusion_day_set(exclusion_commands: ExclusionCommands) -> set[str]:
    """Build a set of excluded day names (e.g., {'Monday', 'Tuesday'}).

    Used for quick validation (can't exclude all 7 days).
    """
    raise NotImplementedError("Implementer: port from date_calculator.py build_exclusion_day_set")


def calculate_rrule_exclusions(
    start_date: datetime,
    end_date: datetime,
    exclusion_commands: ExclusionCommands,
    settings: Settings,
) -> int:
    """Calculate the number of excluded days between start and end.

    Uses dateutil.rrule to generate excluded dates and count them.

    Returns:
        Number of excluded days in the range.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py calculate_rrule_exclusions")


# ── Time interval calculation ─────────────────────────────────────────


def calculate_time_interval(
    interval: str,
    start_datetime: datetime,
    end_datetime: datetime,
) -> tuple[int, datetime]:
    """Calculate how many complete intervals fit between two datetimes.

    Uses arrow.Arrow.range to get a list of interval boundaries,
    then counts them.

    Args:
        interval: 'year', 'month', 'week', 'day', 'hour', 'minute', or 'second'.
        start_datetime: Starting point.
        end_datetime: Ending point.

    Returns:
        Tuple of (count of intervals, last boundary datetime).
    """
    raise NotImplementedError("Implementer: port from date_calculator.py calculate_time_interval")


# ── Normalised output ─────────────────────────────────────────────────


def normalised_days(
    command: SubtractionCommand | TimespanCommand,
    date_time_1: datetime,
    date_time_2: datetime,
) -> str:
    """Calculate the difference between two dates in human-readable format.

    Supports format options:
    - 'long': Full breakdown (years, months, days, hours, minutes, seconds)
    - 'y', 'm', 'w', 'd', 'h', 'M', 's': Individual units
    - 'ymwd': Combined units
    - Default: Most significant non-zero units

    Args:
        command: Command with format option.
        date_time_1: First datetime.
        date_time_2: Second datetime.

    Returns:
        Human-readable difference string (e.g., '7 days, 3 hours').

    Raises:
        FormatError: If format has repeated characters.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py normalised_days")


def valid_command_format(command_format: str) -> bool:
    """Check if a format string has no repeated characters.

    E.g., 'ymwd' is valid, 'yymd' is not (repeated 'y').
    """
    raise NotImplementedError("Implementer: port from date_calculator.py valid_command_format")


# ── Utility helpers ───────────────────────────────────────────────────


def pluralize(count: int | float, singular: str, plural: str) -> str:
    """Return singular or plural form based on count.

    Handles fractional counts (e.g., 1.5 -> plural).
    """
    raise NotImplementedError("Implementer: tiny function, port from humanfriendly pluralize")


def later_date_first(
    date_time_1: datetime, date_time_2: datetime
) -> tuple[datetime, datetime]:
    """Return (earlier, later) datetime pair.

    rrule requires the earlier date first; this ensures correct ordering.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py later_date_last")


def tack_on_time(date_time: datetime) -> datetime:
    """Set the time component of a date to the maximum (23:59:59.999999).

    Used to ensure date-only comparisons work correctly.
    """
    raise NotImplementedError("Implementer: port from date_calculator.py tack_on_time")


def convert_date_time(
    date_time_str: str,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> tuple[datetime, str]:
    """Convert a date/time string to a datetime object and output format.

    Handles:
    - Natural language: "4 hours 8 minutes after 4pm"
    - Week numbers: wn 2015 5 sun
    - Date functions/macros: now, today, tomorrow, easter, etc.
    - User-defined anniversaries
    - Date/time format strings based on settings

    Args:
        date_time_str: Raw date/time string from the parser.
        settings: Workflow settings.
        now_fn: Optional time injection function.

    Returns:
        Tuple of (datetime, output_format_string).

    Raises:
        ValueError: If the string cannot be parsed.
    """
    raise NotImplementedError("Implementer: port from utils.py convert_date_time")
