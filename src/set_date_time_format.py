#!/usr/bin/env python3
"""Set date-time format — action entry point."""

from __future__ import annotations

from src.alfred.io import read_query, write_output
from src.core.mappings import DATE_TIME_MAPPINGS
from src.core.settings import load_settings, save_settings


def main() -> None:
    """Set the date-time separator format preference."""
    query = read_query()
    if query not in DATE_TIME_MAPPINGS:
        write_output("Invalid date/time format")
        return

    settings = load_settings()
    settings.date_time_format = query
    save_settings(settings)
    write_output(f"Date/time format set to {query}")


if __name__ == "__main__":
    main()
