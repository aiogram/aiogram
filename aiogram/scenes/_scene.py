from __future__ import annotations

import inspect
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Tuple, Type, Union, Optional

from typing_extensions import Self

from aiogram import Router, loggers
from aiogram.dispatcher.event.handler import CallableObject, CallbackType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Update

if TYPE_CHECKING:
    from ._wizard import Wizard


class ObserverDecorator:
    def __init__(
        self,
        name: str,
        filters: tuple[CallbackType, ...],
        action: SceneAction | None = None,
        action_after: SceneAction | None = None,
        scene: Union[Scene, str] | None = None,
    ) -> None:
        self.name = name
        self.filters = filters
        self.action = action
        self.action_after = action_after
        self.scene = scene

    def _wrap_class(self, target: Type[Scene]) -> None:
        if not issubclass(target, Scene):
            raise TypeError("Only subclass of Scene is allowed")
        if self.action is not None:
            raise TypeError("This action is not allowed for class")

        filters = getattr(target, "__aiogram_filters__", None)
        if filters is None:
            filters = defaultdict(list)
            setattr(target, "__aiogram_filters__", filters)
        filters[self.name].extend(self.filters)

    def _wrap_filter(self, target: Type[Scene] | CallbackType) -> None:
        handlers = getattr(target, "__aiogram_handler__", None)
        if not handlers:
            handlers = []
            setattr(target, "__aiogram_handler__", handlers)

        handlers.append(
            HandlerContainer(
                self.name,
                target,
                self.filters,
                self.action_after,
                self.scene,
            )
        )

    def _wrap_action(self, target: Type[Scene] | CallbackType) -> None:
        action = getattr(target, "__aiogram_action__", None)
        if action is None:
            action = defaultdict(dict)
            setattr(target, "__aiogram_action__", action)
        action[self.action][self.name] = CallableObject(target)

    def __call__(self, target: Type[Scene] | CallbackType) -> Type[Scene] | CallbackType:
        if inspect.isclass(target):
            self._wrap_class(target)
        elif inspect.isfunction(target):
            if self.action is None:
                self._wrap_filter(target)
            else:
                self._wrap_action(target)
        return target

    def leave(self) -> ActionContainer:
        return ActionContainer(self.name, self.filters, SceneAction.leave)

    def enter(self, target: Type[Scene]) -> ActionContainer:
        return ActionContainer(self.name, self.filters, SceneAction.enter, target)

    def exit(self) -> ActionContainer:
        return ActionContainer(self.name, self.filters, SceneAction.exit)

    def back(self) -> ActionContainer:
        return ActionContainer(self.name, self.filters, SceneAction.back)


class SceneAction(Enum):
    enter = auto()
    leave = auto()
    exit = auto()
    back = auto()


class ActionContainer:
    def __init__(
        self,
        name: str,
        filters: Tuple[CallbackType, ...],
        action: SceneAction,
        target: Type[Scene] | None = None,
    ) -> None:
        self.name = name
        self.filters = filters
        self.action = action
        self.target = target

    async def execute(self, scene: Scene) -> None:
        if self.action == SceneAction.enter and self.target is not None:
            await scene.goto(self.target)
        elif self.action == SceneAction.leave:
            await scene.leave()
        elif self.action == SceneAction.exit:
            await scene.exit()
        elif self.action == SceneAction.back:
            await scene.back()


class HandlerContainer:
    def __init__(
        self,
        name: str,
        handler: CallbackType,
        filters: Tuple[CallbackType, ...],
        action: Optional[SceneAction] = None,
        scene: Optional[Union[Scene, str]] = None,
    ) -> None:
        self.name = name
        self.handler = handler
        self.filters = filters
        self.action_container = ActionContainer(name, filters, action, scene)


@dataclass(slots=True)
class SceneConfig:
    name: str
    filters: Dict[str, List[CallbackType]]
    handlers: List[HandlerContainer]
    actions: Dict[SceneAction, Dict[str, CallableObject]]


class _SceneMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> _SceneMeta:
        state_name = kwargs.pop("state", f"{namespace['__module__']}:{name}")

        filters: defaultdict[str, List[CallbackType]] = defaultdict(list)
        handlers: list[HandlerContainer] = []
        actions: defaultdict[SceneAction, Dict[str, CallableObject]] = defaultdict(dict)

        for base in bases:
            if not isinstance(base, Scene):
                continue
            parent_scene_config = base.__scene_config__

            filters.update(parent_scene_config.filters)
            handlers.extend(parent_scene_config.handlers)
            for action, action_handlers in parent_scene_config.actions.items():
                actions[action].update(action_handlers)

        for name, value in namespace.items():
            if scene_handlers := getattr(value, "__aiogram_handler__", None):
                handlers.extend(scene_handlers)
            elif isinstance(value, ActionContainer):
                handlers.append(HandlerContainer(name, value.execute, value.filters, value.action))
            elif hasattr(value, "__aiogram_action__"):
                for action, action_handlers in value.__aiogram_action__.items():
                    actions[action].update(action_handlers)

        namespace["__scene_config__"] = SceneConfig(
            name=state_name,
            filters=dict(filters),
            handlers=handlers,
            actions=dict(actions),
        )
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class SceneHandlerWrapper:
    def __init__(
        self,
        wizard: Type[Scene],
        handler: CallbackType,
        action_container: Optional[ActionContainer] = None,
    ) -> None:
        self.wizard = wizard
        self.handler = CallableObject(handler)
        self.action_container = action_container

    async def __call__(
        self,
        event: TelegramObject,
        state: FSMContext,
        wizard: Wizard,
        event_update: Update,
        **kwargs: Any,
    ) -> Any:
        scene = self.wizard(
            wizard=wizard,
            update=event_update,
            event=event,
            context=state,
            data=kwargs,
        )
        try:
            return await self.handler.call(
                scene,
                event,
                state=state,
                event_update=event_update,
                wizard=wizard,
                **kwargs,
            )
        finally:
            if self.action_container is not None:
                await self.action_container.execute(scene)

    def __await__(self) -> Self:
        return self


class Scene(metaclass=_SceneMeta):
    __scene_config__: ClassVar[SceneConfig]

    def __init__(
        self,
        wizard: Wizard,
        update: Update,
        event: TelegramObject,
        context: FSMContext,
        data: Dict[str, Any],
    ) -> None:
        self.manager = wizard
        self.update = update
        self.event = event
        self.context = context
        self.data = data

    @classmethod
    def as_router(cls) -> Router:
        scene_config = cls.__scene_config__

        router = Router(name=scene_config.name)
        used_observers = set()

        for observer, filters in scene_config.filters.items():
            router.observers[observer].filter(*filters)
            used_observers.add(observer)

        for handler in scene_config.handlers:
            router.observers[handler.name].register(
                SceneHandlerWrapper(
                    cls,
                    handler.handler,
                    action_container=handler.action_container,
                ),
                *handler.filters,
            )
            used_observers.add(handler.name)

        for observer in used_observers:
            router.observers[observer].filter(StateFilter(scene_config.name))

        return router

    @classmethod
    def as_handler(cls) -> CallbackType:
        async def enter_to_scene_handler(event: TelegramObject, wizard: Wizard) -> None:
            await wizard.enter(cls)

        return enter_to_scene_handler

    async def enter(self, **kwargs: Any) -> None:
        loggers.scene.debug("Entering scene %r", self.__scene_config__.name)
        state = await self.context.get_state()
        await self.context.set_state(self.__scene_config__.name)
        try:
            if not await self._on_action(SceneAction.enter, **kwargs):
                loggers.scene.error(
                    "Enter action not found in scene %r for event %r", self, type(self.event)
                )
        except Exception as e:
            await self.context.set_state(state)
            raise e

    async def leave(self, **kwargs: Any) -> None:
        loggers.scene.debug("Leaving scene %r", self.__scene_config__.name)
        state = await self.context.get_state()
        await self.context.set_state(None)
        try:
            await self._on_action(SceneAction.leave, **kwargs)
        except Exception as e:
            await self.context.set_state(state)
            raise e

    async def exit(self, **kwargs: Any) -> None:
        loggers.scene.debug("Exiting scene %r", self.__scene_config__.name)
        state = await self.context.get_state()
        await self.context.set_state(None)
        try:
            await self._on_action(SceneAction.exit, **kwargs)
        except Exception as e:
            await self.context.set_state(state)
            raise e

    async def back(self, **kwargs: Any) -> None:
        loggers.scene.debug("Back to previous scene from scene %s", self.__scene_config__.name)
        await self.manager.back(**kwargs)

    async def replay(self, event: TelegramObject) -> None:
        await self._on_action(SceneAction.enter, event=event)

    async def goto(self, scene: Union[Type[Scene], str]) -> None:
        await self.manager.enter(scene)

    async def _on_action(self, action: SceneAction, **kwargs: Any) -> bool:
        loggers.scene.debug("Call action %r in scene %r", action.name, self.__scene_config__.name)
        action_config = self.__scene_config__.actions.get(action, {})
        if not action_config:
            loggers.scene.debug(
                "Action %r not found in scene %r", action.name, self.__scene_config__.name
            )
            return False

        event_type = self.update.event_type
        if event_type not in action_config:
            loggers.scene.debug(
                "Action %r for event %r not found in scene %r",
                action.name,
                event_type,
                self.__scene_config__.name,
            )
            return False
        await action_config[event_type].call(self, self.event, **{**self.data, **kwargs})
        return True
