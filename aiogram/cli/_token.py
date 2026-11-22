from __future__ import annotations

import argparse
import os
from pathlib import Path

from aiogram.cli import _output
from aiogram.cli._output import CliError, warn
from aiogram.cli._spec import TOKEN_ENV


def resolve_token(args: argparse.Namespace) -> str:
    """
    The bot token from ``--token-file``, ``--token`` or ``$BOT_TOKEN``, in that order.

    The parser needs :func:`aiogram.cli._spec.add_token_arguments`. The token is never printed.
    """
    if args.token_file is not None:
        try:
            token = Path(args.token_file).read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError) as exc:
            raise CliError(f"cannot read --token-file: {exc}", exit_code=2) from None
    elif args.token is not None:
        warn(f"--token ends up in shell history; prefer --token-file or ${TOKEN_ENV}")
        token = args.token.strip()
    else:
        token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        raise CliError(f"no bot token: set ${TOKEN_ENV} or pass --token-file PATH", exit_code=2)
    _output._secrets.add(token)
    return token
