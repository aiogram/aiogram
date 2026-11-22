"""
Argparse definitions of the built-in ``aiogram`` commands.

This module imports only the standard library, never ``aiogram``: the docs build loads it by
file path to render the CLI reference without importing the package. Built-in handlers are
therefore ``"module:attr"`` strings, which :func:`aiogram.cli.main` imports when the command runs.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from typing import TypeAlias

PROG = "aiogram"
TOKEN_ENV = "BOT_TOKEN"

# Generic only in the stubs, so the alias is a string
Subparsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"


def add_token_arguments(parser: argparse.ArgumentParser) -> None:
    """Add ``--token-file`` / ``--token``; :func:`aiogram.cli._token.resolve_token` reads them."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--token-file",
        metavar="PATH",
        help=f"read the bot token from PATH (default: ${TOKEN_ENV})",
    )
    group.add_argument(
        "--token",
        help=f"bot token; it ends up in shell history, prefer --token-file or ${TOKEN_ENV}",
    )


def register_info(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "info",
        help="show versions and build details for bug reports",
        description="Show aiogram, Rust core and Python versions, the wheel tag and the "
        "installed optional packages.",
    )
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.set_defaults(func="aiogram.cli._info:run")


def register_migrate(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "migrate",
        help="check or rewrite code for aiogram 4.0 (needs aiogram[migrate])",
        description="Report (check) or rewrite (fix) aiogram 3.x code that 4.0 changes.",
    )
    commands = parser.add_subparsers(
        title="commands", metavar="<command>", dest="migrate_command", required=True
    )
    for name, help_text in (
        ("check", "report the code to change; exits 3 on findings"),
        ("fix", "rewrite the code that can be rewritten"),
    ):
        command = commands.add_parser(name, help=help_text, description=help_text.capitalize())
        command.add_argument("paths", nargs="+", metavar="PATH", help="file or directory")
    parser.set_defaults(func="aiogram.cli._migrate:run")


BUILTINS: tuple[Callable[[Subparsers], None], ...] = (register_info, register_migrate)


def build_parser(version: str = "unknown") -> tuple[argparse.ArgumentParser, Subparsers]:
    """Build the root parser with the built-in commands; plugins are added to the second item."""
    parser = argparse.ArgumentParser(prog=PROG, description="aiogram command line interface")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument(
        "--traceback", action="store_true", help="print the full traceback of an error"
    )
    subparsers = parser.add_subparsers(title="commands", metavar="<command>", required=True)
    for register in BUILTINS:
        register(subparsers)
    return parser, subparsers
