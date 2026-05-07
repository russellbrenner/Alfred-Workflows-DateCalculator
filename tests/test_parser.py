"""Tests for the PyPEG2 command parsers."""

from __future__ import annotations

import pytest

from src.core.parser import AnniversaryCommand, MacrosParser, SubtractionCommand, TimespanCommand


@pytest.fixture
def parser(default_settings):
    return DateParser(default_settings)


# Import after fixture declaration keeps the import group intentionally simple for ruff.
from src.core.parser import DateParser  # noqa: E402


@pytest.mark.parametrize(
    ("query", "date_time", "operand_count", "date_format"),
    [
        ("now + 6d", "now", 1, None),
        ("today wn", "today", 0, "wn"),
        ("25.12.14 + 5y 3m", "25.12.14", 1, None),
        ("next mon", "next mon", 0, None),
        ("easter", "easter", 0, None),
    ],
)
def test_timespan_commands(parser, query, date_time, operand_count, date_format):
    command = parser.parse_command(query)

    assert isinstance(command, TimespanCommand)
    assert command.date_time == date_time
    assert len(command.operand_list) == operand_count
    assert command.date_format == date_format


def test_timespan_command_operands(parser):
    command = parser.parse_command("25.12.14 + 5y 3m")

    assert isinstance(command, TimespanCommand)
    assert command.operand_list[0].operator == "+"
    assert [(span.amount, span.span) for span in command.operand_list[0].time_spans] == [("5", "y"), ("3", "m")]


@pytest.mark.parametrize(
    ("query", "date_time_1", "date_time_2", "fmt"),
    [
        ("25.12.14 - 18.01.14", "25.12.14", "18.01.14", ""),
        ("now - christmas", "now", "christmas", ""),
        ("21.06.14@14:20 - 23.01.12@09:21 long", "21.06.14@14:20", "23.01.12@09:21", "long"),
    ],
)
def test_subtraction_commands(parser, query, date_time_1, date_time_2, fmt):
    command = parser.parse_command(query)

    assert isinstance(command, SubtractionCommand)
    assert command.date_time_1 == date_time_1
    assert command.date_time_2 == date_time_2
    assert command.format == fmt


def test_exclusion_command(parser):
    command = parser.parse_command("now + 6d exclude weekdays")

    assert isinstance(command, TimespanCommand)
    assert command.exclusion_commands is not None
    assert command.exclusion_commands.exclusion_keyword == "exclude"
    assert command.exclusion_commands.exclusion_list[0].exclusion_macro == "weekdays"


def test_natural_language_command(parser):
    command = parser.parse_command('"4 hours after 4pm"')

    assert isinstance(command, TimespanCommand)
    assert command.date_time == '"4 hours after 4pm"'


@pytest.mark.parametrize("query", ["wn 2015 5 sun", "wn 7"])
def test_week_number_commands(parser, query):
    command = parser.parse_command(query)

    assert isinstance(command, TimespanCommand)
    assert command.date_time == query


@pytest.mark.parametrize("query", ["*", "#", "<", ">", "&"])
def test_abbreviation_commands(parser, query):
    command = parser.parse_command(query)

    assert isinstance(command, TimespanCommand)
    assert command.date_time == query


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("add birthday 25.12.90", AnniversaryCommand("add", "birthday", "25.12.90")),
        ("delete birthday", AnniversaryCommand("delete", "birthday", None)),
        ("edit birthday 26.12.90", AnniversaryCommand("edit", "birthday", "26.12.90")),
    ],
)
def test_anniversary_commands(default_settings, query, expected):
    command = MacrosParser(default_settings).parse_command(query)

    assert command == expected


@pytest.mark.parametrize("query", ["", "not a real command", "now +", "add"])
def test_error_cases(default_settings, parser, query):
    with pytest.raises(SyntaxError):
        if query == "add":
            MacrosParser(default_settings).parse_command(query)
        else:
            parser.parse_command(query)
