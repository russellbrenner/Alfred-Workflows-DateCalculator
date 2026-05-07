#!/usr/bin/env python3
"""Date format list — Script Filter entry point."""

from __future__ import annotations

from src.alfred.feedback import Feedback
from src.alfred.io import write_feedback
from src.core.mappings import DATE_MAPPINGS
from src.core.settings import load_settings


def main() -> None:
    """List available date formats for selection."""
    settings = load_settings()
    feedback = Feedback()

    for key in sorted(DATE_MAPPINGS):
        is_current = key == settings.date_format
        feedback.add_item(
            title=f"{key} *" if is_current else key,
            subtitle=DATE_MAPPINGS[key]["name"],
            valid=not is_current,
            arg=key,
        )

    write_feedback(feedback)


if __name__ == "__main__":
    main()
