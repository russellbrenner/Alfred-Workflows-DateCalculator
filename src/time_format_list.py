#!/usr/bin/env python3
"""Time format list — Script Filter entry point."""

from __future__ import annotations

from src.alfred.feedback import Feedback
from src.alfred.io import write_feedback
from src.core.mappings import TIME_MAPPINGS
from src.core.settings import load_settings


def main() -> None:
    """List available time formats for selection."""
    settings = load_settings()
    feedback = Feedback()

    for key in sorted(TIME_MAPPINGS):
        is_current = key == settings.time_format
        feedback.add_item(
            title=f"{key} *" if is_current else key,
            subtitle=TIME_MAPPINGS[key]["name"],
            valid=not is_current,
            arg=key,
        )

    write_feedback(feedback)


if __name__ == "__main__":
    main()
