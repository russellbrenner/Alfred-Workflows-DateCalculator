#!/usr/bin/env python3
"""dcalc — Date Calculator main entry point for Alfred Script Filter.

Reads the query from Alfred, parses it, executes the calculation,
and returns JSON feedback for display.
"""

from __future__ import annotations


def main() -> None:
    """Main entry point — wire Alfred input to core engine."""
    raise NotImplementedError("Implementer: load settings, parse query, execute, write feedback")


if __name__ == "__main__":
    main()
