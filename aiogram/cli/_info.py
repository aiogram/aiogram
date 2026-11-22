"""``aiogram info``: everything a bug report needs about this installation."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import sysconfig
from importlib import metadata
from typing import Any

from aiogram.cli._output import paint


def _optional_packages(dist: metadata.Distribution) -> dict[str, str]:
    # Installation metadata doesn't record which extras were requested (R30), so this lists
    # every package an extra can pull in that is installed, whatever installed it.
    found = {}
    for requirement in dist.requires or ():
        spec, _, marker = requirement.partition(";")
        match = re.match(r"[A-Za-z0-9._-]+", spec.strip())
        if "extra" not in marker or match is None:
            continue
        name = re.sub(r"[-_.]+", "-", match.group()).lower()
        try:
            found[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return dict(sorted(found.items()))


def _wheel_tag(dist: metadata.Distribution) -> str | None:
    tags = [
        line.partition(":")[2].strip()
        for line in (dist.read_text("WHEEL") or "").splitlines()
        if line.startswith("Tag:")
    ]
    return ", ".join(tags) or None


def collect() -> tuple[dict[str, Any], str | None]:
    """The ``info`` data and, when the Rust core fails to import, the reason."""
    from aiogram import __version__

    core: dict[str, Any] | None = None
    core_error = None
    try:
        from aiogram._core import build_info

        core = dict(build_info())
    except Exception as exc:  # noqa: BLE001 - info must work on a broken install
        core_error = f"{type(exc).__name__}: {exc}"

    try:
        dist: metadata.Distribution | None = metadata.distribution("aiogram")
    except metadata.PackageNotFoundError:
        dist = None

    is_gil_enabled = getattr(sys, "_is_gil_enabled", None)
    data = {
        "aiogram": __version__,
        "core": core,
        "python": platform.python_version(),
        "implementation": sys.implementation.name,
        "free_threaded": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "gil_enabled": is_gil_enabled() if is_gil_enabled is not None else True,
        "wheel_tag": _wheel_tag(dist) if dist is not None else None,
        "installed_optional_packages": _optional_packages(dist) if dist is not None else {},
    }
    return data, core_error


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def run(args: argparse.Namespace) -> int:
    data, core_error = collect()
    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    core = data["core"]
    if core is not None:
        core_text = (
            f"{core['version']} ({core['profile']}, lto {core['lto']}, {core['target']}, "
            f"pyo3 {core['pyo3_version']})"
        )
    else:
        core_text = f"not loaded ({core_error})"
    rows = [
        ("aiogram", data["aiogram"]),
        ("rust core", core_text),
        ("python", f"{data['python']} ({data['implementation']})"),
        ("free-threaded build", _yes_no(data["free_threaded"])),
        ("GIL enabled", _yes_no(data["gil_enabled"])),
        ("wheel tag", data["wheel_tag"] or "unknown"),
    ]
    for label, value in rows:
        print(f"{paint(label + ':', 'bold', sys.stdout)} {value}")
    print(paint("installed optional packages:", "bold", sys.stdout))
    for name, version in data["installed_optional_packages"].items():
        print(f"  {name} {version}")
    if not data["installed_optional_packages"]:
        print("  (none)")
    return 0
