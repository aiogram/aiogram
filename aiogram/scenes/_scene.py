from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Tuple, Type, Union

from typing_extensions import Self

from aiogram import Router, loggers
from aiogram.dispatcher.event.handler import CallableObject, CallbackType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Update
from ._marker import ActionContainer, SceneAction

if TYPE_CHECKING:
    from ._manager import SceneManager


class _SceneMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> _SceneMeta:
        state_name = kwargs.pop("state", f"{namespace['__module__']}:{name}")

        aiogram_filters: defaultdict[str, List[CallbackType]] = defaultdict(list)
        aiogram_handlers: list[CallbackType] = []
        aiogram_actions: defaultdict[SceneAction, Dict[str, CallableObject]] = defaultdict(dict)

        for base in bases:
            if parent_aiogram_filters := getattr(base, "__aiogram_filters__", None):
                aiogram_filters.update(parent_aiogram_filters)
            if parent_aiogram_handlers := getattr(base, "__aiogram_handlers__", None):
                aiogram_handlers.extend(parent_aiogram_handlers)
            if parent_aiogram_actions := getattr(base, "__aiogram_actions__", None):
                for action, handlers in parent_aiogram_actions.items():
                    aiogram_actions[action].update(handlers)

        for name, value in namespace.items():
            if hasattr(value, "__aiogram_handler__"):
                aiogram_handlers.append(value)
            elif isinstance(value, ActionContainer):
                aiogram_handlers.append(value)
            elif hasattr(value, "__aiogram_action__"):
                for action, handlers in value.__aiogram_action__.items():
                    aiogram_actions[action].update(handlers)

        namespace.update(
            {
                "__aiogram_scene_name__": state_name,
                "__aiogram_filters__": aiogram_filters,
                "__aiogram_handlers__": aiogram_handlers,
                "__aiogram_actions__": aiogram_actions,
            }
        )
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class SceneHandlerWrapper:
    def __init__(self, scene: Type[Scene], handler: CallbackType) -> None:
        self.scene = scene
        self.handler = CallableObject(handler)

    async def __call__(
        self,
        event: TelegramObject,
        state: FSMContext,
        scenes: SceneManager,
        event_update: Update,
        **kwargs: Any,
    ) -> Any:
        scene = self.scene(
            manager=scenes,
            update=event_update,
            event=event,
            context=state,
            data=kwargs,
        )
        return await self.handler.call(
            scene,
            event,
            state=state,
            event_update=event_update,
            scenes=scenes,
            **kwargs,
        )

    def __await__(self) -> Self:
        return self


class Scene(metaclass=_SceneMeta):
    __aiogram_scene_name__: ClassVar[str]
    __aiogram_filters__: ClassVar[Dict[str, List[CallbackType]]]
    __aiogram_handlers__: ClassVar[List[CallbackType]]
    __aiogram_actions__: ClassVar[Dict[SceneAction, Dict[str, CallableObject]]]

    def __init__(
        self,
        manager: SceneManager,
        update: Update,
        event: TelegramObject,
        context: FSMContext,
        data: Dict[str, Any],
    ) -> None:
        self.manager = manager
        self.update = update
        self.event = event
        self.context = context
        self.data = data

    @classmethod
    def as_router(cls) -> Router:
        router = Router(name=cls.__aiogram_scene_name__)
        used_observers = set()

        for observer, filters in cls.__aiogram_filters__.items():
            router.observers[observer].filter(*filters)
            used_observers.add(observer)

        for handler in cls.__aiogram_handlers__:
            handler_filters = getattr(handler, "__aiogram_filters__", None)
            if not handler_filters:
                continue
            for observer, filters in handler_filters.items():
                router.observers[observer].register(SceneHandlerWrapper(cls, handler), *filters)
                used_observers.add(observer)

        for observer in used_observers:
            router.observers[observer].filter(StateFilter(cls.__aiogram_scene_name__))

        return router

    @classmethod
    def as_handler(cls) -> CallbackType:
        async def enter_to_scene_handler(event: TelegramObject, scenes: SceneManager) -> None:
            await scenes.enter(cls)

        return enter_to_scene_handler

    async def enter(self, **kwargs: Any) -> None:
        loggers.scene.debug("Entering scene %s", self.__aiogram_scene_name__)
        state = await self.context.get_state()
        await self.context.set_state(self.__aiogram_scene_name__)
        try:
            if not await self._on_action(SceneAction.enter, **kwargs):
                loggers.scene.error(
                    "Enter action not found in scene %s for event %r", self, type(self.event)
                )
        except Exception as e:
            await self.context.set_state(state)
            raise e

    async def leave(self, **kwargs: Any) -> None:
        loggers.scene.debug("Leaving scene %s", self.__aiogram_scene_name__)
        state = await self.context.get_state()
        await self.context.set_state(None)
        try:
            await self._on_action(SceneAction.leave, **kwargs)
        except Exception as e:
            await self.context.set_state(state)
            raise e

    async def exit(self, **kwargs: Any) -> None:
        loggers.scene.debug("Exiting scene %s", self.__aiogram_scene_name__)
        state = await self.context.get_state()
        await self.context.set_state(None)
        try:
            await self._on_action(SceneAction.exit, **kwargs)
        except Exception as e:
            await self.context.set_state(state)
            raise e

    async def back(self, **kwargs: Any) -> None:
        loggers.scene.debug("Back to previous scene from scene %s", self.__aiogram_scene_name__)
        await self.manager.back(**kwargs)

    async def replay(self, event: TelegramObject) -> None:
        await self._on_action(SceneAction.enter, event=event)

    async def goto(self, scene: Union[Type[Scene], str]) -> None:
        await self.manager.enter(scene)

    async def _on_action(self, action: SceneAction, **kwargs: Any) -> bool:
        loggers.scene.debug("Call action %r in scene %r", action.name, self.__aiogram_scene_name__)
        action_config = self.__aiogram_actions__.get(action, {})
        if not action_config:
            loggers.scene.debug(
                "Action %r not found in scene %r", action.name, self.__aiogram_scene_name__
            )
            return False

        event_type = self.update.event_type
        if event_type not in action_config:
            loggers.scene.debug(
                "Action %r for event %r not found in scene %r",
                action.name,
                event_type,
                self.__aiogram_scene_name__,
            )
            return False

        await action_config[event_type].call(self, self.event, **{**self.data, **kwargs})
        return True
