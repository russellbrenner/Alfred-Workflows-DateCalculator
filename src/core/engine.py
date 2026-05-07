"""Date arithmetic engine — pure functions for computation."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from datetime import date, datetime, timedelta

import arrow
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, YEARLY, rrule, rruleset

from src.core.formatters import DATE_FORMATTERS_MAP
from src.core.functions import (
    DATE_FUNCTION_MAP,
    DAYS_OF_WEEK_ABBREVIATIONS,
    EXCLUSION_MAP,
    get_date_format,
    get_full_format,
    get_time_format,
    get_time_preprocessor,
)
from src.core.mappings import MAX_LOOKAHEAD_ATTEMPTS, TIME_CALCULATION, VALID_FORMAT_OPTIONS, WN_FUNCTION_REGEX
from src.core.parser import ExclusionCommands, SubtractionCommand, TimespanCommand
from src.core.settings import Settings


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


def execute_command(
    command: TimespanCommand | SubtractionCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Execute a parsed command and return the result string."""
    if isinstance(command, SubtractionCommand):
        return do_subtraction(command, settings, now_fn)
    if isinstance(command, TimespanCommand):
        output = do_timespans(command, settings, now_fn)
        if command.date_format:
            if command.exclusion_commands:
                raise IncompatibleFunctionError
            return do_formats(
                TimespanCommand(date_time=output, operand_list=[], date_format=command.date_format),
                settings,
                now_fn,
            )
        return output
    raise TypeError(f"Unsupported command type: {type(command)!r}")


def do_timespans(
    command: TimespanCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Process a timespan command (e.g., 'now + 6d')."""
    date_time, output_format = convert_date_time(command.date_time, settings, now_fn)
    original_date_time = date_time
    date_time = delta_arithmetic(date_time, command.operand_list)
    date_time = exclusion_check(original_date_time, date_time, command, settings)
    return date_time.strftime(output_format)


def do_subtraction(
    command: SubtractionCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Process a subtraction command (e.g., '25.12.14 - 18.01.14')."""
    date_time_1, _ = convert_date_time(command.date_time_1, settings, now_fn)
    date_time_2, _ = convert_date_time(command.date_time_2, settings, now_fn)
    date_time_1 = delta_arithmetic(date_time_1, command.operand_list_1 or [])
    date_time_2 = delta_arithmetic(date_time_2, command.operand_list_2 or [])
    return normalised_days(command, date_time_1, date_time_2)


def do_formats(
    command: TimespanCommand,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> str:
    """Apply a format function to a datetime string."""
    date_time, _ = convert_date_time(command.date_time, settings, now_fn)
    formatter = DATE_FORMATTERS_MAP.get((command.date_format or "").lower())
    if formatter is None:
        return "Invalid function . . . "
    return formatter(date_time)


def delta_arithmetic(date_time: datetime, operand_list: list) -> datetime:
    """Apply a list of operands to a datetime via relativedelta."""
    delta_date_time = date_time
    for operand in operand_list:
        for timespan in operand.time_spans:
            delta_operand = relativedelta(
                seconds=int(timespan.amount) if timespan.span == "s" else 0,
                minutes=int(timespan.amount) if timespan.span == "M" else 0,
                hours=int(timespan.amount) if timespan.span == "h" else 0,
                days=int(timespan.amount) if timespan.span == "d" else 0,
                weeks=int(timespan.amount) if timespan.span == "w" else 0,
                months=int(timespan.amount) if timespan.span == "m" else 0,
                years=int(timespan.amount) if timespan.span == "y" else 0,
            )
            if operand.operator == "+":
                delta_date_time += delta_operand
            else:
                delta_date_time -= delta_operand
    return delta_date_time


def exclusion_check(
    original_date_time: datetime,
    date_time: datetime,
    command: TimespanCommand,
    settings: Settings,
) -> datetime:
    """Apply exclusion rules if present on the command."""
    if command.exclusion_commands is None:
        return date_time

    exclusion_day_set = build_exclusion_day_set(command.exclusion_commands)
    if len(exclusion_day_set) >= 7:
        raise ExclusionNoDaysFoundError

    starting_date_time = original_date_time
    lookahead_date = date_time
    lookahead_count = 0
    extra_days = calculate_rrule_exclusions(starting_date_time, lookahead_date, command.exclusion_commands, settings)

    while extra_days > 0:
        starting_date_time = lookahead_date
        lookahead_date = lookahead_date + timedelta(days=extra_days)
        lookahead_count += 1
        if lookahead_count >= MAX_LOOKAHEAD_ATTEMPTS:
            raise ExclusionTooFarAheadError
        extra_days = calculate_rrule_exclusions(starting_date_time, lookahead_date, command.exclusion_commands, settings)

    return lookahead_date


def build_exclusion_day_set(exclusion_commands: ExclusionCommands) -> set[str]:
    """Build a set of excluded day names."""
    excluded_days: set[str] = set()
    for exclusion_type in exclusion_commands.exclusion_list:
        if exclusion_type.exclusion_macro is not None:
            macro = exclusion_type.exclusion_macro.lower()
            excluded_days.update(EXCLUSION_MAP[macro]["days"])
    return excluded_days


def calculate_rrule_exclusions(
    start_date: datetime,
    end_date: datetime,
    exclusion_commands: ExclusionCommands,
    settings: Settings,
) -> int:
    """Calculate the number of excluded days between start and end."""
    exclusion_ruleset = rruleset()
    for exclusion_type in exclusion_commands.exclusion_list:
        if exclusion_type.exclusion_range is not None:
            from_date, _ = convert_date_time(exclusion_type.exclusion_range.from_datetime, settings)
            to_date, _ = convert_date_time(exclusion_type.exclusion_range.to_datetime, settings)
            exclusion_ruleset.rrule(rrule(freq=DAILY, dtstart=from_date, until=to_date))
        elif exclusion_type.exclusion_datetime is not None:
            real_date, _ = convert_date_time(exclusion_type.exclusion_datetime, settings)
            exclusion_ruleset.rrule(rrule(freq=DAILY, dtstart=real_date, until=real_date))
        elif exclusion_type.exclusion_macro is not None:
            macro = exclusion_type.exclusion_macro.lower()
            rule_factory = EXCLUSION_MAP[macro]["rule"]
            exclusion_ruleset.rrule(rule_factory(start=start_date, end=end_date))
        else:
            raise UnknownExclusionTypeError

    return len(list(exclusion_ruleset.between(after=start_date, before=end_date, inc=True)))


def calculate_time_interval(interval: str, start_datetime: datetime, end_datetime: datetime) -> tuple[int, datetime]:
    """Calculate how many complete intervals fit between two datetimes."""
    datetime_list = list(arrow.Arrow.range(interval, start_datetime, end_datetime))
    if datetime_list:
        return len(datetime_list) - 1, datetime_list[-1].datetime.replace(tzinfo=None)
    return 0, start_datetime


def normalised_days(
    command: SubtractionCommand | TimespanCommand,
    date_time_1: datetime,
    date_time_2: datetime,
) -> str:
    """Calculate the difference between two dates in human-readable format."""
    command_format = getattr(command, "format", "") or ""
    if not valid_command_format(command_format):
        raise FormatError

    if command_format == "long":
        difference = relativedelta(date_time_1, date_time_2)
        return "{years}, {months}, {days}, {hours}, {minutes}, {seconds}".format(
            years=pluralize(abs(difference.years), TIME_CALCULATION["y"]["singular"], TIME_CALCULATION["y"]["plural"]),
            months=pluralize(abs(difference.months), TIME_CALCULATION["m"]["singular"], TIME_CALCULATION["m"]["plural"]),
            days=pluralize(abs(difference.days), TIME_CALCULATION["d"]["singular"], TIME_CALCULATION["d"]["plural"]),
            hours=pluralize(abs(difference.hours), TIME_CALCULATION["h"]["singular"], TIME_CALCULATION["h"]["plural"]),
            minutes=pluralize(abs(difference.minutes), TIME_CALCULATION["M"]["singular"], TIME_CALCULATION["M"]["plural"]),
            seconds=pluralize(abs(difference.seconds), TIME_CALCULATION["s"]["singular"], TIME_CALCULATION["s"]["plural"]),
        )

    date_1, date_2 = later_date_first(date_time_1, date_time_2)
    start_date_time = arrow.get(date_1).datetime.replace(tzinfo=None)
    end_date_time = arrow.get(date_2).datetime.replace(tzinfo=None)

    if command_format:
        ordered_format_options = [option for option in VALID_FORMAT_OPTIONS if option in command_format]
        show_zero_items = True
    else:
        ordered_format_options = VALID_FORMAT_OPTIONS
        show_zero_items = False

    normalised_elements: list[str] = []
    for option in ordered_format_options:
        count, start_date_time = calculate_time_interval(TIME_CALCULATION[option]["interval"], start_date_time, end_date_time)
        if option == ordered_format_options[-1]:
            fractional = abs((end_date_time - start_date_time).total_seconds()) / TIME_CALCULATION[option]["seconds"]
            count += fractional
        if (show_zero_items or count > 0) and TIME_CALCULATION[option]["interval"] != "second":
            normalised_elements.append(pluralize(round_number(count), TIME_CALCULATION[option]["singular"], TIME_CALCULATION[option]["plural"]))
    return ", ".join(normalised_elements)


def valid_command_format(command_format: str) -> bool:
    """Check if a format string has no repeated characters."""
    return not any(count > 1 for count in Counter(command_format).values())


def pluralize(count: int | float, singular: str, plural: str) -> str:
    """Return a human-friendly count with singular/plural unit."""
    return f"{count} {singular if count == 1 else plural}"


def round_number(number: float) -> int | float:
    """Round whole floats to ints; keep meaningful fractions compact."""
    if int(number) == number:
        return int(number)
    return round(number, 2)


def later_date_first(date_time_1: datetime, date_time_2: datetime) -> tuple[datetime, datetime]:
    """Return (earlier, later) datetime pair."""
    if date_time_1 < date_time_2:
        return date_time_1, date_time_2
    return date_time_2, date_time_1


def tack_on_time(date_time: datetime | date) -> datetime:
    """Set the time component of a date to the maximum."""
    return datetime.combine(date_time, datetime.max.time())


def get_anniversary(date_object: datetime, now_fn: Callable[[], datetime] | None = None) -> datetime:
    anniversary_rule = rrule(
        bymonthday=date_object.day,
        bymonth=date_object.month,
        freq=YEARLY,
        dtstart=date_object,
    )
    current_date = (now_fn or datetime.today)()
    anniversary_date = anniversary_rule.after(current_date, inc=False)
    return datetime.combine(anniversary_date, datetime.min.time())


def process_macros(
    date_time_str: str,
    anniversaries: dict[str, str],
    now_fn: Callable[[], datetime] | None = None,
) -> datetime | None:
    """Resolve user anniversary macros."""
    absolute = False
    if date_time_str.startswith("^"):
        date_time_str = date_time_str.lstrip("^")
        absolute = True

    for anniversary, anniversary_date_str in anniversaries.items():
        if date_time_str.lower() == anniversary.lower():
            anniversary_date = dateutil.parser.parse(anniversary_date_str)
            if absolute:
                return anniversary_date
            return get_anniversary(anniversary_date, now_fn)
    return None


def natural_parser(
    date_time: str,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> tuple[datetime, str]:
    """Parse quoted natural-language expressions."""
    format_map = {1: get_date_format(settings), 2: get_time_format(settings), 3: get_full_format(settings)}
    date_time_to_parse = date_time[1:-1]

    try:
        import parsedatetime as pdt

        cal = pdt.Calendar()
        parsed_dt, error_code = cal.parseDT(date_time_to_parse, sourceTime=now_fn() if now_fn else None)
        if error_code == 0:
            raise ValueError
        return parsed_dt, format_map.get(error_code, get_full_format(settings))
    except ImportError:
        default = now_fn() if now_fn else datetime.now()
        parsed_dt = dateutil.parser.parse(date_time_to_parse, default=default, fuzzy=True)
        has_time = bool(re.search(r"\d\s*(?::\d{2})?\s*(am|pm)\b|\d{1,2}:\d{2}", date_time_to_parse, re.I))
        date_words = r"\b(today|tomorrow|yesterday|mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b"
        has_date_word = bool(re.search(date_words, date_time_to_parse, re.I))
        if has_time and has_date_word:
            return parsed_dt, get_full_format(settings)
        if has_time:
            return parsed_dt, get_time_format(settings)
        return parsed_dt, get_date_format(settings)


def get_date_from_week_number(date_time: str, now_fn: Callable[[], datetime] | None = None) -> datetime:
    """Return a date from an ISO week command via date.fromisocalendar."""
    week_day_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    current_date = (now_fn() if now_fn else datetime.today()).date()
    match = re.match(WN_FUNCTION_REGEX, date_time)
    if match is None:
        raise ValueError
    year = int(match.group("year")) if match.group("year") is not None else current_date.year
    week_number = int(match.group("week_number")) if match.group("week_number") is not None else int(current_date.strftime("%V"))
    day = match.group("day") if match.group("day") is not None else week_day_map[current_date.weekday()]
    weekday = list(DAYS_OF_WEEK_ABBREVIATIONS).index(day.lower()) + 1
    return datetime.combine(date.fromisocalendar(year, week_number, weekday), datetime.min.time())


def convert_date_time(
    date_time_str: str,
    settings: Settings,
    now_fn: Callable[[], datetime] | None = None,
) -> tuple[datetime, str]:
    """Convert a date/time string to a datetime object and output format."""
    date_format = get_date_format(settings)
    time_format = get_time_format(settings)
    full_format = get_full_format(settings)

    if not date_time_str:
        raise ValueError
    if date_time_str[0] == '"':
        return natural_parser(date_time_str, settings, now_fn)
    if date_time_str.lower().startswith("wn"):
        return get_date_from_week_number(date_time_str, now_fn), date_format

    raw_str = str(date_time_str)
    lower_str = raw_str.lower()
    if lower_str in DATE_FUNCTION_MAP:
        return _date_function_with_optional_now(lower_str, settings, now_fn)

    anniversary_date = process_macros(lower_str, settings.anniversaries, now_fn)
    if anniversary_date is not None:
        return datetime.combine(anniversary_date, datetime.max.time()), date_format

    try:
        time_preprocessor = get_time_preprocessor(settings)
        processed = time_preprocessor(raw_str) if time_preprocessor else raw_str
        return datetime.strptime(processed.upper(), full_format), full_format
    except ValueError:
        pass

    try:
        process_date = datetime.strptime(raw_str.upper(), date_format)
        return datetime.combine(process_date, datetime.max.time()), date_format
    except ValueError:
        pass

    try:
        processed = get_time_preprocessor(settings)(raw_str)
        process_time = datetime.strptime(processed.upper(), time_format).time()
        base = now_fn() if now_fn else datetime.today()
        return datetime.combine(base, process_time), time_format
    except ValueError as exc:
        raise ValueError from exc


def _date_function_with_optional_now(
    key: str,
    settings: Settings,
    now_fn: Callable[[], datetime] | None,
) -> tuple[datetime, str]:
    """Evaluate date functions, honoring now_fn for the common deterministic helpers."""
    if now_fn is None:
        return DATE_FUNCTION_MAP[key](settings)

    current = now_fn()
    date_only = datetime.combine(current.date(), datetime.max.time())
    if key in {"date", "today", "*"}:
        return date_only, get_date_format(settings)
    if key in {"time", "&"}:
        return datetime.combine(current.date(), current.time()), get_time_format(settings)
    if key in {"now", "#"}:
        return current, get_full_format(settings)
    if key in {"yesterday", "<"}:
        return date_only - timedelta(days=1), get_date_format(settings)
    if key in {"tomorrow", ">"}:
        return date_only + timedelta(days=1), get_date_format(settings)
    # Less common special-date helpers still use their legacy direct datetime.now() semantics.
    return DATE_FUNCTION_MAP[key](settings)
