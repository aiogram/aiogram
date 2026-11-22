"""
The ``aiogram`` command line (``aiogram ...`` and ``python -m aiogram ...``).

Plugins register commands through the ``aiogram.cli`` entry-point group::

    [project.entry-points."aiogram.cli"]
    hello = "aiogram_hello:register"

``register(subparsers)`` receives the subparsers action, adds its commands with ``add_parser``
and sets each handler with ``set_defaults(func=handler)``. A handler takes the parsed
``argparse.Namespace`` and returns the exit code (``None`` means 0), or raises :class:`CliError`.

Exit codes: 0 ok, 1 runtime error, 2 usage error, 3 findings (``migrate check``).
"""

from __future__ import annotations

import importlib
import sys
import traceback
from collections.abc import Sequence

from aiogram.cli._output import CliError, error
from aiogram.cli._plugins import load_plugins
from aiogram.cli._spec import build_parser
from aiogram.cli._token import redact

__all__ = ["CliError", "main"]


def main(argv: Sequence[str] | None = None) -> int:
    from aiogram import __version__

    parser, subparsers = build_parser(__version__)
    load_plugins(subparsers)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # --help, --version and usage errors
        return exc.code if isinstance(exc.code, int) else int(exc.code is not None)

    try:
        func = getattr(args, "func", None)
        if func is None:  # a plugin command without set_defaults(func=...)
            raise CliError("this command has no handler")
        if isinstance(func, str):
            module, _, attr = func.partition(":")
            func = getattr(importlib.import_module(module), attr)
        return func(args) or 0
    except CliError as exc:
        error(redact(str(exc)))
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - reported as exit code 1
        if args.traceback:
            sys.stderr.write(redact(traceback.format_exc()))
        error(redact(f"{type(exc).__name__}: {exc}"))
        return 1
