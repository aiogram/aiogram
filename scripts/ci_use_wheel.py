"""Make this checkout importable with the native extension taken from a prebuilt wheel (CI).

Copies ``aiogram/_core.*`` (the ``.so`` / ``.pyd``) out of the single wheel in ``<dir>`` next to
``aiogram/_core/`` and adds the checkout to the running interpreter's ``sys.path`` with a
``.pth`` file: the layout ``maturin develop`` leaves. The wheel's ``*.dist-info`` goes into
site-packages too: pytest finds the ``pytest11`` entry point (``aiogram.test``) through it. The
Python sources stay the checkout's own, so a wheel cached on the Rust inputs (tests.yml,
``build-wheels``; ``pyproject.toml`` is in the key, so the metadata is current) is never stale
and coverage paths stay repository-relative.

Usage: ``uv run python scripts/ci_use_wheel.py <dir>``
"""

from __future__ import annotations

import sys
import sysconfig
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(directory: str) -> None:
    (wheel,) = Path(directory).glob("*.whl")
    site = Path(sysconfig.get_path("purelib"))
    with zipfile.ZipFile(wheel) as archive:
        (member,) = (n for n in archive.namelist() if n.startswith("aiogram/_core."))
        (ROOT / member).write_bytes(archive.read(member))
        archive.extractall(site, [n for n in archive.namelist() if ".dist-info/" in n])
    (site / "aiogram_checkout.pth").write_text(f"{ROOT}\n")
    print(f"{wheel.name}: {member} -> {ROOT}")


if __name__ == "__main__":
    main(*sys.argv[1:])
