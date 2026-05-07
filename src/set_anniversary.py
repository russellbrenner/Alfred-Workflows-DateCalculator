#!/usr/bin/env python3
"""Set anniversary — add/edit/delete entry point."""
from __future__ import annotations

from src.alfred.io import read_query, write_output


def main() -> None:
    """Add, edit, or delete an anniversary."""
    raise NotImplementedError("Implementer: parse command, modify settings, print output")


if __name__ == "__main__":
    main()
