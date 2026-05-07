#!/usr/bin/env python3
"""Time format list — Script Filter entry point."""
from __future__ import annotations

from src.alfred.io import write_feedback
from src.alfred.feedback import Feedback


def main() -> None:
    """List available time formats for selection."""
    raise NotImplementedError("Implementer: load settings, list formats with current marked, write feedback")


if __name__ == "__main__":
    main()
