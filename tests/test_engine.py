from datetime import datetime

import pytest

from src.core.engine import FormatError, convert_date_time, execute_command, normalised_days
from src.core.parser import DateParser, SubtractionCommand
from src.core.settings import Settings


@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def parser(settings):
    return DateParser(settings)


def fixed_now():
    return datetime(2014, 12, 24, 13, 45, 0)


def test_convert_default_date(settings):
    dt, output_format = convert_date_time("25.12.14", settings, fixed_now)
    assert dt == datetime.combine(datetime(2014, 12, 25), datetime.max.time())
    assert output_format == "%d.%m.%y"


def test_convert_date_functions_and_abbreviations(settings):
    now_dt, now_format = convert_date_time("now", settings, fixed_now)
    today_dt, today_format = convert_date_time("today", settings, fixed_now)
    time_dt, time_format = convert_date_time("time", settings, fixed_now)
    tomorrow_dt, _ = convert_date_time("tomorrow", settings, fixed_now)
    star_dt, _ = convert_date_time("*", settings, fixed_now)
    amp_dt, _ = convert_date_time("&", settings, fixed_now)
    hash_dt, _ = convert_date_time("#", settings, fixed_now)
    lt_dt, _ = convert_date_time("<", settings, fixed_now)
    gt_dt, _ = convert_date_time(">", settings, fixed_now)

    assert now_dt == fixed_now()
    assert now_format == "%d.%m.%y@%H:%M"
    assert today_dt == datetime.combine(fixed_now().date(), datetime.max.time())
    assert today_format == "%d.%m.%y"
    assert time_dt == fixed_now()
    assert time_format == "%H:%M"
    assert tomorrow_dt.date().isoformat() == "2014-12-25"
    assert star_dt == today_dt
    assert amp_dt == time_dt
    assert hash_dt == now_dt
    assert lt_dt.date().isoformat() == "2014-12-23"
    assert gt_dt == tomorrow_dt


def test_quoted_natural_parse_does_not_crash(settings):
    dt, output_format = convert_date_time('"25 Dec 2014"', settings, fixed_now)
    assert dt.year == 2014
    assert output_format in {"%d.%m.%y", "%d.%m.%y@%H:%M"}


def test_subtraction_produces_non_empty_days_result(parser, settings):
    result = execute_command(parser.parse_command("25.12.14 - 18.01.14"), settings, fixed_now)
    assert result
    assert "month" in result or "week" in result or "day" in result


def test_subtraction_days_format_exact(parser, settings):
    result = execute_command(parser.parse_command("25.12.14 - 18.01.14 d"), settings, fixed_now)
    assert result == "341 days"


def test_timespan_addition_returns_formatted_date(parser, settings):
    result = execute_command(parser.parse_command("25.12.14 + 6d"), settings, fixed_now)
    assert result == "31.12.14"


def test_invalid_repeated_format_triggers_format_error():
    command = SubtractionCommand("25.12.14", [], "18.01.14", [], "dd")
    with pytest.raises(FormatError):
        normalised_days(command, datetime(2014, 12, 25), datetime(2014, 1, 18))
