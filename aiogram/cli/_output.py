from __future__ import annotations

import os
import re
import sys
from typing import TextIO

from aiogram.cli._spec import PROG

_STYLES = {"bold": "1", "red": "31", "yellow": "33"}

# Secret parts of the tokens ``_token.resolve_token`` returned (the text after ``<bot id>:``),
# masked in every warning and error (D66). The mask is a constant, so no printed text is
# derived from a token.
_hidden: set[str] = set()
# Anything shaped like a bot token, for text holding a token the CLI never resolved
# (an argparse diagnostic quoting a misplaced --token value, a plugin's exception)
_TOKEN_SHAPE = re.compile(r"\b(\d{5,}):[A-Za-z0-9_-]{30,}")


def redact(text: str) -> str:
    """Replace every resolved or token-shaped string in ``text`` with ``<bot id>:***``."""
    for value in _hidden:
        text = text.replace(value, "***")
    return _TOKEN_SHAPE.sub(r"\1:***", text)


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
    print(f"{PROG}: {paint('warning', 'yellow', sys.stderr)}: {redact(message)}", file=sys.stderr)


def error(message: str) -> None:
    print(f"{PROG}: {paint('error', 'red', sys.stderr)}: {redact(message)}", file=sys.stderr)
