"""Command dataclasses and PyPEG2 parsers for date calculator commands.

Each dataclass represents a parsed command variant. The PyPEG2 grammar in
DateParser produces a parse tree, which is then converted into these typed
command dataclasses for the rest of the workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pypeg2 import List, attr, maybe_some, optional, parse, some


@dataclass
class TimeSpan:
    """A single time span element: amount + unit (e.g., '6d', '3w')."""

    amount: str  # numeric amount as string
    span: str  # unit character: y, m, w, d, h, M, s


@dataclass
class Operand:
    """An operand: operator + list of TimeSpans (e.g., '+ 6d 3w')."""

    operator: str  # '+' or '-'
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

    action: str  # 'add', 'edit', 'delete'
    anniversary_name: str
    date_time: str | None = None


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
        settings: Workflow settings dict or Settings dataclass for regex patterns.
    """

    # Parser-only fallbacks keep the grammar useful while src.core.functions is
    # being ported. They mirror the legacy keys; runtime execution still uses
    # DATE_FUNCTION_MAP/EXCLUSION_MAP and can be completed independently.
    _FALLBACK_DATE_FUNCTIONS = (
        "pancake day",
        "next month",
        "start year",
        "start bst",
        "prev mon",
        "prev tue",
        "prev wed",
        "prev thu",
        "prev fri",
        "prev sat",
        "prev sun",
        "next mon",
        "next tue",
        "next wed",
        "next thu",
        "next fri",
        "next sat",
        "next sun",
        "end year",
        "end bst",
        "yesterday",
        "tomorrow",
        "passover",
        "easter",
        "today",
        "date",
        "time",
        "now",
        "lent",
        "mlk",
        "mum",
        "mom",
        "mutter",
        "*",
        "&",
        "#",
        "<",
        ">",
    )
    _FALLBACK_EXCLUSION_MACROS = (
        "all except weekdays",
        "all except weekends",
        "all except mondays",
        "all except tuesdays",
        "all except wednesdays",
        "all except thursdays",
        "all except fridays",
        "all except saturdays",
        "all except sundays",
        "weekdays",
        "weekends",
        "mondays",
        "tuesdays",
        "wednesdays",
        "thursdays",
        "fridays",
        "saturdays",
        "sundays",
        "xwkdy",
        "xwknd",
        "xmon",
        "xtue",
        "xwed",
        "xthu",
        "xfri",
        "xsat",
        "xsun",
        "wkdy",
        "wknd",
        "mon",
        "tue",
        "wed",
        "thu",
        "fri",
        "sat",
        "sun",
    )

    def __init__(self, settings: dict[str, Any] | Any) -> None:
        # Import here to avoid circular imports at module load time.
        from src.core.formatters import DATE_FORMATTERS_MAP
        from src.core.functions import DATE_FUNCTION_MAP, EXCLUSION_MAP
        from src.core.mappings import DATE_MAPPINGS, DATE_TIME_MAPPINGS, TIME_MAPPINGS, WN_FUNCTION_REGEX

        self.settings = settings

        date_fmt = DATE_MAPPINGS[self._setting("date-format", "date_format")]["regex"]
        time_fmt = TIME_MAPPINGS[self._setting("time-format", "time_format")]["regex"]
        date_time_fmt = DATE_TIME_MAPPINGS[self._setting("date-time-format", "date_time_format")]["date-time-format"](date_fmt, time_fmt)

        self.date_re = re.compile(date_fmt, re.IGNORECASE)
        self.time_re = re.compile(time_fmt, re.IGNORECASE)
        self.date_time_re = re.compile(date_time_fmt, re.IGNORECASE)
        self.date_functions_re = self._compile_alternation((*DATE_FUNCTION_MAP.keys(), *self._FALLBACK_DATE_FUNCTIONS), re.IGNORECASE)
        self.user_macros_re = self._compile_alternation((f"\\^?{re.escape(str(x))}" for x in self._anniversaries()), re.IGNORECASE, pre_escaped=True)
        self.operator_re = re.compile(r"[+-]")
        self.time_span_re = re.compile(r"[ymwdhMs]")
        self.time_digits_re = re.compile(r"[0-9]+")
        self.format_re = re.compile(r"[ymwdhMs]+|long")
        self.date_formatters_re = self._compile_alternation(DATE_FORMATTERS_MAP.keys(), re.IGNORECASE)

        self.exclusion_keyword_re = re.compile(r"exclude|ex|x", re.IGNORECASE)
        self.exclusion_macro_re = self._compile_alternation((*EXCLUSION_MAP.keys(), *self._FALLBACK_EXCLUSION_MACROS), re.IGNORECASE)
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
        if not command_string or not command_string.strip():
            raise SyntaxError("empty command")

        class Operator(str):
            grammar = self.operator_re

        class TimeSpans(str):
            grammar = attr("amount", self.time_digits_re), attr("span", self.time_span_re)

        class OperandTree(str):
            grammar = attr("operator", Operator), attr("timeSpans", some(TimeSpans))

        class OperandList(List):
            grammar = maybe_some(OperandTree)

        class DateFormat(str):
            grammar = self.date_formatters_re

        class DateTimeTree(str):
            grammar = [
                self.date_time_re,
                self.date_re,
                self.time_re,
                self.date_functions_re,
                self.user_macros_re,
                self.parseable_date_re,
                self.wn_command_re,
            ]

        class Format(str):
            grammar = optional(self.format_re)

        class ExclusionKeyword(str):
            grammar = self.exclusion_keyword_re

        class ExclusionRangeTree(str):
            grammar = (
                attr("fromDateTime", DateTimeTree),
                self.exclusion_range_operator_re,
                attr("toDateTime", DateTimeTree),
            )

        class ExclusionTypeTree(List):
            grammar = [
                attr("exclusionRange", ExclusionRangeTree),
                attr("exclusionMacro", self.exclusion_macro_re),
                attr("exclusionDateTime", DateTimeTree),
            ]

        class ExclusionList(List):
            grammar = some(ExclusionTypeTree)

        class ExclusionCommandsTree(str):
            grammar = attr("exclusionKeyword", ExclusionKeyword), attr("exclusionList", ExclusionList)

        class Commands(str):
            grammar = [
                (
                    attr("dateTime1", DateTimeTree),
                    attr("operandList1", OperandList),
                    "-",
                    attr("dateTime2", DateTimeTree),
                    attr("operandList2", OperandList),
                    attr("format", Format),
                ),
                (attr("dateTime", DateTimeTree), attr("operandList", OperandList), attr("dateFormat", DateFormat)),
                (
                    attr("dateTime", DateTimeTree),
                    attr("operandList", OperandList),
                    attr("exclusionCommands", ExclusionCommandsTree),
                    attr("dateFormat", DateFormat),
                ),
                (
                    attr("dateTime", DateTimeTree),
                    attr("operandList", OperandList),
                    attr("exclusionCommands", ExclusionCommandsTree),
                ),
                (attr("dateTime", DateTimeTree), attr("dateFormat", DateFormat)),
                (attr("dateTime", DateTimeTree), attr("operandList", OperandList)),
            ]

        parsed = parse(command_string.strip(), Commands)
        return self._convert_command(parsed)

    def _setting(self, dict_key: str, attr_name: str) -> Any:
        if isinstance(self.settings, dict):
            return self.settings[dict_key]
        return getattr(self.settings, attr_name)

    def _anniversaries(self) -> dict[str, str]:
        if isinstance(self.settings, dict):
            return self.settings.get("anniversaries", {})
        return getattr(self.settings, "anniversaries", {})

    @staticmethod
    def _compile_alternation(values: Any, flags: int = 0, *, pre_escaped: bool = False) -> re.Pattern[str]:
        unique_values = {str(value) for value in values if str(value)}
        if not unique_values:
            return re.compile(r"(?!)")
        sorted_values = sorted(unique_values, key=len, reverse=True)
        parts = sorted_values if pre_escaped else [re.escape(x) for x in sorted_values]
        return re.compile("|".join(parts), flags)

    @staticmethod
    def _convert_operands(operand_list: Any) -> list[Operand]:
        return [
            Operand(
                operator=str(operand.operator),
                time_spans=[TimeSpan(amount=str(span.amount), span=str(span.span)) for span in operand.timeSpans],
            )
            for operand in (operand_list or [])
        ]

    @classmethod
    def _convert_exclusion_commands(cls, exclusion_commands: Any) -> ExclusionCommands:
        exclusions = []
        for exclusion in exclusion_commands.exclusionList:
            if hasattr(exclusion, "exclusionRange"):
                exclusion_range = exclusion.exclusionRange
                exclusions.append(
                    ExclusionType(
                        exclusion_range=ExclusionRange(
                            from_datetime=str(exclusion_range.fromDateTime),
                            to_datetime=str(exclusion_range.toDateTime),
                        )
                    )
                )
            elif hasattr(exclusion, "exclusionMacro"):
                exclusions.append(ExclusionType(exclusion_macro=str(exclusion.exclusionMacro)))
            elif hasattr(exclusion, "exclusionDateTime"):
                exclusions.append(ExclusionType(exclusion_datetime=str(exclusion.exclusionDateTime)))
        return ExclusionCommands(exclusion_keyword=str(exclusion_commands.exclusionKeyword), exclusion_list=exclusions)

    def _convert_command(self, parsed: Any) -> TimespanCommand | SubtractionCommand:
        if hasattr(parsed, "dateTime1"):
            return SubtractionCommand(
                date_time_1=str(parsed.dateTime1),
                operand_list_1=self._convert_operands(parsed.operandList1),
                date_time_2=str(parsed.dateTime2),
                operand_list_2=self._convert_operands(parsed.operandList2),
                format=str(parsed.format) if str(parsed.format) else "",
            )

        return TimespanCommand(
            date_time=str(parsed.dateTime),
            operand_list=self._convert_operands(getattr(parsed, "operandList", [])),
            date_format=str(parsed.dateFormat) if hasattr(parsed, "dateFormat") and str(parsed.dateFormat) else None,
            exclusion_commands=self._convert_exclusion_commands(parsed.exclusionCommands) if hasattr(parsed, "exclusionCommands") else None,
        )


class MacrosParser(DateParser):
    """PEG parser for anniversary add/edit/delete commands.

    Extends DateParser with grammar for:
        add <name> <dateTime>
        edit <name> <dateTime>
        delete <name>
    """

    def __init__(self, settings: dict[str, Any] | Any) -> None:
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
        if not command_string or not command_string.strip():
            raise SyntaxError("empty command")

        class DateTimeTree(str):
            grammar = optional(
                [
                    self.date_time_re,
                    self.date_re,
                    self.time_re,
                    self.date_functions_re,
                    self.user_macros_re,
                ]
            )

        class AnniversaryName(str):
            grammar = self.anniversary_name_re

        class Add(str):
            grammar = self.add_command_re

        class Delete(str):
            grammar = self.delete_command_re

        class Edit(str):
            grammar = self.edit_command_re

        class Commands(List):
            grammar = [
                (attr("delete", Delete), attr("anniversaryName", AnniversaryName)),
                (attr("edit", Edit), attr("anniversaryName", AnniversaryName), attr("dateTime", DateTimeTree)),
                (attr("add", Add), attr("anniversaryName", AnniversaryName), attr("dateTime", DateTimeTree)),
            ]

        parsed = parse(command_string.strip(), Commands)
        if hasattr(parsed, "delete"):
            return AnniversaryCommand(action=str(parsed.delete), anniversary_name=str(parsed.anniversaryName))
        if hasattr(parsed, "edit"):
            return AnniversaryCommand(
                action=str(parsed.edit),
                anniversary_name=str(parsed.anniversaryName),
                date_time=str(parsed.dateTime) or None,
            )
        return AnniversaryCommand(
            action=str(parsed.add),
            anniversary_name=str(parsed.anniversaryName),
            date_time=str(parsed.dateTime) or None,
        )
