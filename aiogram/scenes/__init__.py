from __future__ import annotations

__all__ = [
    "Scene",
    "SceneRegistry",
    "Wizard",
    "on",
]

from ._wizard import Wizard
from ._marker import OnMarker
from ._registry import SceneRegistry
from ._scene import Scene

on = OnMarker()
