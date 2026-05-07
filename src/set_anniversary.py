#!/usr/bin/env python3
"""Set anniversary — add/edit/delete entry point."""

from __future__ import annotations

from src.alfred.io import read_query, write_output
from src.core.engine import convert_date_time
from src.core.mappings import DATE_MAPPINGS
from src.core.parser import AnniversaryCommand, MacrosParser
from src.core.settings import Settings, load_settings, save_settings

FOUR_DIGIT_DATE_ERROR = "Please ensure that you have set your date format to one that supports 4-digit years"


def _requires_four_digit_year(settings: Settings) -> bool:
    return "%Y" in DATE_MAPPINGS[settings.date_format]["date_format"]


def _add_anniversary(command: AnniversaryCommand, settings: Settings) -> str:
    name = command.anniversary_name.lower()
    if not _requires_four_digit_year(settings):
        return FOUR_DIGIT_DATE_ERROR
    if name in settings.anniversaries:
        return f"{name} already exists"

    date_time, _ = convert_date_time(command.date_time or "", settings)
    settings.anniversaries[name] = date_time.isoformat()
    save_settings(settings)
    return f"{name} added"


def _edit_anniversary(command: AnniversaryCommand, settings: Settings) -> str:
    name = command.anniversary_name.lower()
    if not _requires_four_digit_year(settings):
        return FOUR_DIGIT_DATE_ERROR
    if name not in settings.anniversaries:
        return f"{name} does not exist"

    date_time, _ = convert_date_time(command.date_time or "", settings)
    settings.anniversaries[name] = date_time.isoformat()
    save_settings(settings)
    return f"{name} changed"


def _delete_anniversary(command: AnniversaryCommand, settings: Settings) -> str:
    name = command.anniversary_name.lower()
    if name not in settings.anniversaries:
        return f"{name} does not exist"

    del settings.anniversaries[name]
    save_settings(settings)
    return f"{name} deleted"


def main() -> None:
    """Add, edit, or delete an anniversary."""
    settings = load_settings()
    try:
        command = MacrosParser(settings).parse_command(read_query())
        action = command.action.lower()
        if action == "add":
            output = _add_anniversary(command, settings)
        elif action == "edit":
            output = _edit_anniversary(command, settings)
        elif action == "delete":
            output = _delete_anniversary(command, settings)
        else:
            output = "Invalid Command"
    except SyntaxError:
        output = "Invalid Command"
    except ValueError:
        output = "Invalid Date"

    write_output(output)


if __name__ == "__main__":
    main()
