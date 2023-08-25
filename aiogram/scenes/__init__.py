from __future__ import annotations

__all__ = [
    "Scene",
    "SceneRegistry",
    "SceneManager",
    "on",
]

from ._manager import SceneManager
from ._marker import OnMarker
from ._registry import SceneRegistry
from ._scene import Scene

on = OnMarker()
