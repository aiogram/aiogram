"""Side adapters: cases call aiogram only through these, so a 4.0 adapter can sit beside 3.x.

``aiogram3`` is the 3.x adapter (A-05); B-02 adds ``aiogram4`` exposing the same functions.
"""

from __future__ import annotations

import importlib
from types import ModuleType


def load() -> ModuleType:
    import aiogram

    major = aiogram.__version__.split(".", 1)[0]
    return importlib.import_module(f"benchmarks.adapters.aiogram{major}")
