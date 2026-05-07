#!/usr/bin/env python3
"""Anniversary list — Script Filter entry point."""
from __future__ import annotations

from src.alfred.io import read_query, write_feedback
from src.alfred.feedback import Feedback


def main() -> None:
    """List anniversaries as Alfred Script Filter results."""
    raise NotImplementedError("Implementer: load settings, list anniversaries, write feedback")


if __name__ == "__main__":
    main()
