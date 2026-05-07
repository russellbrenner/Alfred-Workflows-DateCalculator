#!/usr/bin/env python3
"""Anniversary list — Script Filter entry point."""

from __future__ import annotations

import dateutil.parser

from src.alfred.feedback import Feedback
from src.alfred.io import read_query, write_feedback
from src.core.mappings import DATE_MAPPINGS
from src.core.settings import load_settings


def main() -> None:
    """List anniversaries as Alfred Script Filter results."""
    settings = load_settings()
    query = read_query().lower()
    date_format = DATE_MAPPINGS[settings.date_format]["date_format"]

    feedback = Feedback()
    for name in sorted(settings.anniversaries):
        if query and not name.lower().startswith(query):
            continue
        date_time = dateutil.parser.parse(settings.anniversaries[name])
        feedback.add_item(
            title=f"{name} ➤ {date_time.strftime(date_format)}",
            subtitle="Press alt to change, ctrl to delete",
            arg=name,
            valid=True,
            mods={
                "alt": {"valid": True, "arg": f"edit {name} ", "subtitle": "Edit entry"},
                "ctrl": {"valid": True, "arg": f"delete {name}", "subtitle": "Delete entry"},
            },
        )

    write_feedback(feedback)


if __name__ == "__main__":
    main()
