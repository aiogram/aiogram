"""``aiogram migrate``: the namespace only; the engine is ``aiogram.migrate``."""

from __future__ import annotations

import argparse
import importlib

from aiogram.cli._output import CliError


def run(args: argparse.Namespace) -> int:
    try:
        engine = importlib.import_module("aiogram.migrate")
    except ModuleNotFoundError as exc:
        missing = (exc.name or "").partition(".")[0]
        if missing == "libcst":
            raise CliError(
                "aiogram migrate needs libcst: pip install 'aiogram[migrate]'", exit_code=2
            ) from None
        if exc.name == "aiogram.migrate":
            raise CliError("aiogram migrate is not available in this build", exit_code=2) from None
        raise
    result: int = engine.run(args)
    return result
