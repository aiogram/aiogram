from __future__ import annotations

import os
import sys
from typing import TextIO

from aiogram.cli._spec import PROG

_STYLES = {"bold": "1", "red": "31", "yellow": "33"}


class CliError(Exception):
    """An expected failure: ``main`` prints the message and exits with ``exit_code``."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def paint(text: str, style: str, stream: TextIO) -> str:
    """ANSI-style ``text`` when ``stream`` is a terminal and ``NO_COLOR`` is unset or empty."""
    if os.environ.get("NO_COLOR") or not stream.isatty():
        return text
    return f"\033[{_STYLES[style]}m{text}\033[0m"


def warn(message: str) -> None:
    print(f"{PROG}: {paint('warning', 'yellow', sys.stderr)}: {message}", file=sys.stderr)


def error(message: str) -> None:
    print(f"{PROG}: {paint('error', 'red', sys.stderr)}: {message}", file=sys.stderr)
