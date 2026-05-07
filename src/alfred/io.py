"""Alfred workflow I/O — argument reading and output writing.

Handles sys.argv parsing for Alfred's Script Filter and Run Script objects,
and stdout writing for JSON feedback and plain text output.
"""

from __future__ import annotations

import sys

from src.alfred.feedback import Feedback


def read_args() -> list[str]:
    """Read command-line arguments from Alfred.

    Alfred passes arguments as sys.argv[1:]. For Script Filter objects
    with `scriptargtype=1`, the full query is a single argument.
    For older formats (scriptargtype=0), arguments may be split.

    Returns:
        List of argument strings (usually [query] or []).
    """
    return sys.argv[1:]


def read_query() -> str:
    """Read the single query string from Alfred.

    Returns empty string if no arguments provided.
    """
    args = read_args()
    return args[0] if args else ""


def write_feedback(fb: Feedback) -> None:
    """Write Feedback as JSON to stdout for Alfred Script Filter.

    Alfred reads stdout from Script Filter scripts and parses it as
    JSON (when type=json is set in the workflow object).
    """
    sys.stdout.write(fb.to_json())
    sys.stdout.write("\n")


def write_output(text: str) -> None:
    """Write plain text output to stdout for Run Script actions.

    Used for action scripts that print text (notifications, clipboard, etc.)
    """
    print(text)
