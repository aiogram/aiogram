from __future__ import annotations

import inspect
from typing import Any, Dict, Optional, Type, Union

from aiogram import Router

from ..dispatcher.event.bases import NextMiddlewareType
from ..types import TelegramObject
from ._wizard import Wizard
from ._scene import Scene


class SceneRegistry:
    def __init__(self, router: Router) -> None:
        self.router = router

        for observer in router.observers.values():
            if observer.event_name in {"update", "error"}:
                continue
            observer.outer_middleware(self._middleware)

        self._scenes: Dict[str, Type[Scene]] = {}

    async def _middleware(
        self,
        handler: NextMiddlewareType[TelegramObject],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["wizard"] = Wizard(
            registry=self,
            update=data["event_update"],
            event=event,
            context=data["state"],
            data=data,
        )
        return await handler(event, data)

    def add(self, *scenes: Type[Scene], router: Optional[Router] = None) -> None:
        if router is None:
            router = self.router

        for scene in scenes:
            if scene.__aiogram_scene_name__ in self._scenes:
                raise ValueError(f"Scene {scene.__aiogram_scene_name__} already exists")

            self._scenes[scene.__aiogram_scene_name__] = scene

            router.include_router(scene.as_router())

    def get(self, scene: Union[Type[Scene], str]) -> Type[Scene]:
        if inspect.isclass(scene) and issubclass(scene, Scene):
            target = scene.__aiogram_scene_name__
            check_class = True
        else:
            target = scene
            check_class = False

        if not isinstance(target, str):
            raise TypeError("Scene must be a string or subclass of Scene")
        try:
            result = self._scenes[target]
        except KeyError:
            raise ValueError(f"Scene {scene!r} is not registered")

        if check_class and not issubclass(result, scene):
            raise ValueError(f"Scene {scene!r} is not registered")

        return result
