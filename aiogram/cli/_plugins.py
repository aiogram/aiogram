"""Third-party commands from the ``aiogram.cli`` entry-point group."""

from __future__ import annotations

import argparse
from importlib.metadata import EntryPoint, entry_points
from typing import Any

from aiogram.cli._output import warn
from aiogram.cli._spec import PROG, Subparsers

GROUP = "aiogram.cli"
BUILTIN = "aiogram (built-in)"


class _Guard:
    """
    The subparsers action as one plugin sees it: ``add_parser`` skips names already taken.

    Built-in commands are registered first and plugins load in sorted entry-point-name order, so
    built-ins always win, then the first plugin. A skipped command gets a detached parser, so the
    plugin's ``register`` still runs to the end.
    """

    def __init__(self, action: Subparsers, owners: dict[str, str], owner: str) -> None:
        self._action = action
        self._owners = owners
        self._owner = owner

    def add_parser(self, name: str, **kwargs: Any) -> argparse.ArgumentParser:
        if name in self._owners:
            self._shadowed(name)
            return argparse.ArgumentParser(prog=f"{PROG} {name}", add_help=False)
        aliases = []
        for alias in kwargs.pop("aliases", ()):
            if alias in self._owners:
                self._shadowed(alias)
            else:
                aliases.append(alias)
        parser: argparse.ArgumentParser = self._action.add_parser(name, aliases=aliases, **kwargs)
        for taken in (name, *aliases):
            self._owners[taken] = self._owner
        return parser

    def _shadowed(self, name: str) -> None:
        warn(f"command '{name}' of {self._owner} is ignored: {self._owners[name]} provides it")

    def __getattr__(self, item: str) -> Any:
        return getattr(self._action, item)


def _describe(entry_point: EntryPoint) -> str:
    dist = entry_point.dist.name if entry_point.dist is not None else "unknown distribution"
    return f"plugin '{entry_point.name}' ({dist})"


def load_plugins(subparsers: Subparsers) -> None:
    """Let every ``aiogram.cli`` plugin register its commands; a failing one is reported."""
    owners = dict.fromkeys(subparsers.choices, BUILTIN)
    for entry_point in sorted(entry_points(group=GROUP), key=lambda ep: ep.name):
        owner = _describe(entry_point)
        try:
            entry_point.load()(_Guard(subparsers, owners, owner))
        except Exception as exc:  # noqa: BLE001 - a broken plugin must not break other commands
            warn(f"{owner} failed to load: {type(exc).__name__}: {exc}")
