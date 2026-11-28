"""``import.aiogram``: a cold ``import aiogram`` in a fresh interpreter (startup included)."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

from benchmarks.harness import REGISTRY, Ctx


@REGISTRY.case("import.aiogram")
def import_aiogram(ctx: Ctx) -> Any:
    ctx.entry("import.aiogram")
    args = [sys.executable, "-I", "-c", "import aiogram"]
    return lambda: subprocess.run(args, check=True)
