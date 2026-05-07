#!/usr/bin/env python3
"""Set time format — action entry point."""

from __future__ import annotations

from src.alfred.io import read_query, write_output
from src.core.mappings import TIME_MAPPINGS
from src.core.settings import load_settings, save_settings


def main() -> None:
    """Set the time format preference."""
    query = read_query()
    if query not in TIME_MAPPINGS:
        write_output("Invalid time format")
        return

    settings = load_settings()
    settings.time_format = query
    save_settings(settings)
    write_output(f"Time format set to {query}")


if __name__ == "__main__":
    main()
