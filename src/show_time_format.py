#!/usr/bin/env python3
"""Show time format — display current setting."""

from __future__ import annotations

from src.alfred.io import write_output
from src.core.settings import load_settings


def main() -> None:
    """Display the current time format setting."""
    settings = load_settings()
    write_output(f"Time format is {settings.time_format}")


if __name__ == "__main__":
    main()
