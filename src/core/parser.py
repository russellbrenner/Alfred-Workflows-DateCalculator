"""Command dataclasses for the date calculator parser.

Each dataclass represents a parsed command variant. The PyPEG2 grammar
in DateParser produces instances of these classes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import re
from pypeg2 import List, attr, parse, optional, some, maybe_some


class DateParser:
    """PEG parser for date calculator commands.

    Uses pypeg2 to parse command strings into typed Command dataclasses.

    The grammar supports:
    - Timespan commands: `dateTime [+|- operandList] [format]`
    - Subtraction commands: `dateTime1 [-] dateTime2 [format]`
    - Exclusion commands: `dateTime [+ operandList] exclude [exclusions]`
    - Format-only commands: `dateTime format`
    - Natural language: `"natural language expression"`
    - Week number commands: `wn [year] [week] [day]`
    - Abbreviations: `<` `*` `>` `&` `#`

    Args:
        settings: Workflow settings dict for regex patterns.
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        # Import here to avoid circular imports at module load time
        from src.core.mappings import (
            WN_FUNCTION_REGEX,
            DATE_MAPPINGS,
            TIME_MAPPINGS,
            DATE_TIME_MAPPINGS,
        )
        from src.core.functions import DATE_FUNCTION_MAP, DAYS_OF_WEEK_ABBREVIATIONS, EXCLUSION_MAP
        from src.core.formatters import DATE_FORMATTERS_MAP

        self.settings = settings

        # Build regex patterns from settings
        date_fmt = DATE_MAPPINGS[settings["date-format"]]["regex"]
        time_fmt = TIME_MAPPINGS[settings["time-format"]]["regex"]
        date_time_fmt = DATE_TIME_MAPPINGS[settings["date-time-format"]]["date-time-format"](
            date_fmt, time_fmt
        )

        self.date_re = re.compile(date_fmt, re.IGNORECASE)
        self.time_re = re.compile(time_fmt, re.IGNORECASE)
        self.date_time_re = re.compile(date_time_fmt, re.IGNORECASE)
        self.date_functions_re = re.compile(
            "|".join(re.escape(str(x)) for x in DATE_FUNCTION_MAP.keys()), re.IGNORECASE
        )
        self.user_macros_re = re.compile(
            "|".join("\\^?" + str(x) for x in settings["anniversaries"].keys()), re.IGNORECASE
        )
        self.operator_re = re.compile(r"[+-]")
        self.time_span_re = re.compile(r"[ymwdhMs]")
        self.time_digits_re = re.compile(r"[0-9]+")
        self.format_re = re.compile(r"[ymwdhMs]+|long")
        self.date_formatters_re = re.compile(
            "|".join(re.escape(str(x)) for x in DATE_FORMATTERS_MAP.keys()), re.IGNORECASE
        )
        self.exclusion_keyword_re = re.compile(r"exclude|ex|x")
        self.exclusion_macro_re = re.compile(
            "|".join(re.escape(str(x)) for x in EXCLUSION_MAP.keys()), re.IGNORECASE
        )
        self.exclusion_range_operator_re = re.compile(r"to|until", re.IGNORECASE)
        self.parseable_date_re = re.compile(r'"[^"]+"', re.IGNORECASE)
        self.wn_command_re = WN_FUNCTION_REGEX

    def parse_command(self, command_string: str) -> TimespanCommand | SubtractionCommand:
        """Parse a command string into a typed command object.

        Args:
            command_string: Raw input from Alfred (e.g., 'now + 6d').

        Returns:
            A TimespanCommand or SubtractionCommand dataclass instance.

        Raises:
            SyntaxError: If the command string doesn't match any valid grammar.
        """
        raise NotImplementedError("Implementer: port PyPEG2 grammar from date_parser.py")


class MacrosParser(DateParser):
    """PEG parser for anniversary add/edit/delete commands.

    Extends DateParser with grammar for:
        add <name> <dateTime>
        edit <name> <dateTime>
        delete <name>
    """

    def __init__(self, settings: dict[str, Any]) -> None:
        super().__init__(settings)
        self.anniversary_name_re = re.compile(r"[a-z_]{2,}", re.IGNORECASE)
        self.add_command_re = re.compile(r"add", re.IGNORECASE)
        self.delete_command_re = re.compile(r"delete", re.IGNORECASE)
        self.edit_command_re = re.compile(r"edit", re.IGNORECASE)

    def parse_command(self, command_string: str) -> AnniversaryCommand:
        """Parse an anniversary command string.

        Args:
            command_string: Raw input (e.g., 'add birthday 25.12.90').

        Returns:
            An AnniversaryCommand dataclass instance.

        Raises:
            SyntaxError: If the command string doesn't match any valid grammar.
        """
        raise NotImplementedError("Implementer: port PyPEG2 grammar from macros_parser.py")


@dataclass
class TimeSpan:
    """A single time span element: amount + unit (e.g., '6d', '3w')."""
    amount: str  # numeric amount as string
    span: str    # unit character: y, m, w, d, h, M, s


@dataclass
class Operand:
    """An operand: operator + list of TimeSpans (e.g., '+ 6d 3w')."""
    operator: str       # '+' or '-'
    time_spans: list[TimeSpan]


@dataclass
class DateTime:
    """A date/time expression string (raw from parser)."""
    value: str


@dataclass
class ExclusionRange:
    """An exclusion range: from_date to/until to_date."""
    from_datetime: str
    to_datetime: str


@dataclass
class ExclusionType:
    """A single exclusion: either a range, a datetime, or a macro."""
    exclusion_range: ExclusionRange | None = None
    exclusion_datetime: str | None = None
    exclusion_macro: str | None = None


@dataclass
class ExclusionCommands:
    """Container for exclusion keyword + list of exclusion types."""
    exclusion_keyword: str
    exclusion_list: list[ExclusionType]


# ── Command variants ──────────────────────────────────────────────────


@dataclass
class TimespanCommand:
    """Command: dateTime + operandList [+ dateFormat].

    Examples:
        dcalc now + 6d
        dcalc 25.12.14 + 5y 3m
        dcalc today wn
        dcalc now + 6d long
    """
    date_time: str
    operand_list: list[Operand]
    date_format: str | None = None
    exclusion_commands: ExclusionCommands | None = None


@dataclass
class SubtractionCommand:
    """Command: dateTime1 - dateTime2 [+ format].

    Examples:
        dcalc 25.12.14 - 18.01.14
        dcalc now - christmas
        dcalc 21.06.14@14:20 - 23.01.12@09:21 long
    """
    date_time_1: str
    operand_list_1: list[Operand] | None
    date_time_2: str
    operand_list_2: list[Operand] | None
    format: str  # format option: 'y', 'ymwd', 'long', etc.


@dataclass
class AnniversaryCommand:
    """Command: add/edit/delete anniversaryName [+ dateTime].

    Examples:
        dcalcset list add birthday 25.12.90
        dcalcset list edit birthday 26.12.90
        dcalcset list delete birthday
    """
    action: str       # 'add', 'edit', 'delete'
    anniversary_name: str
    date_time: str | None = None
