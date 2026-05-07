#!/usr/bin/env python3
"""dcalc — Date Calculator main entry point for Alfred Script Filter."""

from __future__ import annotations

from src.alfred.feedback import Feedback
from src.alfred.io import read_query, write_feedback
from src.core.engine import (
    ExclusionNoDaysFoundError,
    ExclusionTooFarAheadError,
    FormatError,
    IncompatibleFunctionError,
    UnknownExclusionTypeError,
    execute_command,
)
from src.core.parser import DateParser
from src.core.settings import load_settings

HELP_TEXT = "Enter a date calculation, e.g. now + 6d or 25.12.14 - 18.01.14"


_ENGINE_ERROR_MESSAGES = {
    IncompatibleFunctionError: "Invalid command - Don't use exclusions and formats together.",
    UnknownExclusionTypeError: "Invalid exclusion - Try again.",
    ExclusionNoDaysFoundError: "All days excluded",
    ExclusionTooFarAheadError: "That's too far into the future",
}

_ERROR_STRINGS = {
    "Invalid function . . .",
    "Invalid function . . . ",
    "Invalid expression",
    "Invalid Command",
    "Invalid Date/time",
    "Invalid format",
    "All days excluded",
    "That's too far into the future",
}


def _add_result_item(feedback: Feedback, output: str, query: str) -> None:
    if output.startswith("Invalid") or output in _ERROR_STRINGS:
        feedback.add_item(title=". . .", subtitle=output, arg=query, valid=False)
    else:
        feedback.add_item(title=output, subtitle="Copy to clipboard", arg=output, valid=True)


def main() -> None:
    """Read Alfred input, execute the date calculation, and write JSON feedback."""
    query = read_query()
    feedback = Feedback()

    if not query.strip():
        feedback.add_item(title="Date Calculator", subtitle=HELP_TEXT, arg=query, valid=False)
        write_feedback(feedback)
        return

    settings = load_settings()
    try:
        command = DateParser(settings).parse_command(query)
        output = execute_command(command, settings)
    except SyntaxError:
        output = "Invalid Command"
    except ValueError:
        output = "Invalid Date/time"
    except FormatError:
        output = "Invalid format"
    except tuple(_ENGINE_ERROR_MESSAGES) as exc:
        output = _ENGINE_ERROR_MESSAGES[type(exc)]

    _add_result_item(feedback, output, query)
    write_feedback(feedback)


if __name__ == "__main__":
    main()
