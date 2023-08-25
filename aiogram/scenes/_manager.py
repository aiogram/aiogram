from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Update
from ._history import HistoryManager

if TYPE_CHECKING:
    from ._registry import SceneRegistry
    from ._scene import Scene


class SceneManager:
    def __init__(
        self,
        registry: SceneRegistry,
        update: Update,
        event: TelegramObject,
        context: FSMContext,
        data: dict[str, Any],
    ) -> None:
        self.registry = registry
        self.update = update
        self.event = event
        self.context = context
        self.data = data

        self._history = HistoryManager(self.context)

    async def _get_scene(self, scene_type: type[Scene] | str) -> Scene:
        scene_type = self.registry.get(scene_type)
        return scene_type(
            manager=self,
            update=self.update,
            event=self.event,
            context=self.context,
            data=self.data,
        )

    async def _get_active_scene(self) -> Scene | None:
        state = await self.context.get_state()
        if state is None:
            return None
        return await self._get_scene(state)

    async def enter(self, scene_type: type[Scene] | str, **kwargs: Any) -> None:
        active_scene = await self._get_active_scene()
        if active_scene is not None:
            await active_scene.leave(**kwargs)
        scene = await self._get_scene(scene_type)
        await scene.enter(**kwargs)
        await self._history.snapshot()

    async def leave(self, **kwargs: Any) -> None:
        try:
            scene = await self._get_active_scene()
        except ValueError:
            return
        if not scene:
            return
        await scene.leave(**kwargs)

    async def exit(self, **kwargs: Any) -> None:
        try:
            scene = await self._get_active_scene()
        except ValueError:
            return
        if not scene:
            return
        await scene.exit(**kwargs)
        await self._history.clear()

    async def back(self, **kwargs: Any) -> None:
        previous_state = await self._history.rollback()
        if previous_state is not None:
            await self.enter(previous_state, **kwargs)
        else:
            await self.exit(**kwargs)
