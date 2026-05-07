#!/usr/bin/env python3
"""Date-time format list — Script Filter entry point."""

from __future__ import annotations

from datetime import datetime

from src.alfred.feedback import Feedback
from src.alfred.io import write_feedback
from src.core.mappings import DATE_MAPPINGS, DATE_TIME_MAPPINGS, TIME_MAPPINGS
from src.core.settings import load_settings


def _example(now: datetime, key: str, date_format: str, time_format: str) -> str:
    date = now.strftime(date_format)
    time = now.strftime(time_format)
    return DATE_TIME_MAPPINGS[key]["date-time-format"](date, time)


def main() -> None:
    """List available date-time separator formats for selection."""
    settings = load_settings()
    feedback = Feedback()
    now = datetime.now()
    date_format = DATE_MAPPINGS[settings.date_format]["date_format"]
    time_format = TIME_MAPPINGS[settings.time_format]["time_format"]

    for key in sorted(DATE_TIME_MAPPINGS):
        is_current = key == settings.date_time_format
        feedback.add_item(
            title=f"{key} *" if is_current else key,
            subtitle=_example(now, key, date_format, time_format),
            valid=not is_current,
            arg=key,
        )

    write_feedback(feedback)


if __name__ == "__main__":
    main()
