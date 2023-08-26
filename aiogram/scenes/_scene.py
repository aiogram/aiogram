from __future__ import annotations

import inspect
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from typing_extensions import Self

from aiogram import Router, loggers
from aiogram.dispatcher.event.bases import NextMiddlewareType
from aiogram.dispatcher.event.handler import CallableObject, CallbackType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.scenes._history import HistoryManager
from aiogram.types import TelegramObject, Update


class ObserverDecorator:
    def __init__(
        self,
        name: str,
        filters: tuple[CallbackType, ...],
        action: SceneAction | None = None,
        after: Optional[After] = None,
    ) -> None:
        self.name = name
        self.filters = filters
        self.action = action
        self.after = after

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
                name=self.name,
                handler=target,
                filters=self.filters,
                after=self.after,
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
        target: Optional[Union[Type[Scene], str]] = None,
    ) -> None:
        self.name = name
        self.filters = filters
        self.action = action
        self.target = target

    async def execute(self, wizard: SceneWizard) -> None:
        if self.action == SceneAction.enter and self.target is not None:
            await wizard.goto(self.target)
        elif self.action == SceneAction.leave:
            await wizard.leave()
        elif self.action == SceneAction.exit:
            await wizard.exit()
        elif self.action == SceneAction.back:
            await wizard.back()


class HandlerContainer:
    def __init__(
        self,
        name: str,
        handler: CallbackType,
        filters: Tuple[CallbackType, ...],
        after: Optional[After] = None,
    ) -> None:
        self.name = name
        self.handler = handler
        self.filters = filters
        self.after = after


@dataclass()
class SceneConfig:
    state: Optional[str]
    filters: Dict[str, List[CallbackType]]
    handlers: List[HandlerContainer]
    actions: Dict[SceneAction, Dict[str, CallableObject]]


async def _empty_handler(*args: Any, **kwargs: Any) -> None:
    pass


class _SceneMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> _SceneMeta:
        state_name = kwargs.pop("state", None)
        filters: defaultdict[str, List[CallbackType]] = defaultdict(list)
        handlers: list[HandlerContainer] = []
        actions: defaultdict[SceneAction, Dict[str, CallableObject]] = defaultdict(dict)

        for base in bases:
            if not issubclass(base, Scene):
                continue
            parent_scene_config = base.__scene_config__

            filters.update(parent_scene_config.filters)
            handlers.extend(parent_scene_config.handlers)
            for action, action_handlers in parent_scene_config.actions.items():
                actions[action].update(action_handlers)

        for name, value in namespace.items():
            if scene_handlers := getattr(value, "__aiogram_handler__", None):
                handlers.extend(scene_handlers)
            if isinstance(value, ObserverDecorator):
                handlers.append(
                    HandlerContainer(
                        value.name,
                        _empty_handler,
                        value.filters,
                        after=value.after,
                    )
                )
            if hasattr(value, "__aiogram_action__"):
                for action, action_handlers in value.__aiogram_action__.items():
                    actions[action].update(action_handlers)

        namespace["__scene_config__"] = SceneConfig(
            state=state_name,
            filters=dict(filters),
            handlers=handlers,
            actions=dict(actions),
        )
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class SceneHandlerWrapper:
    def __init__(
        self,
        scene: Type[Scene],
        handler: CallbackType,
        after: Optional[After] = None,
    ) -> None:
        self.scene = scene
        self.handler = CallableObject(handler)
        self.after = after

    async def __call__(
        self,
        event: TelegramObject,
        state: FSMContext,
        scenes: ScenesManager,
        event_update: Update,
        **kwargs: Any,
    ) -> Any:
        scene = self.scene(
            wizard=SceneWizard(
                scene_config=self.scene.__scene_config__,
                manager=scenes,
                state=state,
                update_type=event_update.event_type,
                event=event,
                data=kwargs,
            )
        )

        result = await self.handler.call(
            scene,
            event,
            state=state,
            event_update=event_update,
            **kwargs,
        )
        if self.after:
            action_container = ActionContainer(
                "after",
                (),
                self.after.action,
                self.after.scene,
            )
            await action_container.execute(scene.wizard)
        return result

    def __await__(self) -> Self:
        return self


class Scene(metaclass=_SceneMeta):
    __scene_config__: ClassVar[SceneConfig]

    def __init__(
        self,
        wizard: SceneWizard,
    ) -> None:
        self.wizard = wizard
        self.wizard.scene = self

    @classmethod
    def add_to_router(cls, router: Router) -> None:
        scene_config = cls.__scene_config__
        used_observers = set()

        for observer, filters in scene_config.filters.items():
            router.observers[observer].filter(*filters)
            used_observers.add(observer)

        for handler in scene_config.handlers:
            router.observers[handler.name].register(
                SceneHandlerWrapper(
                    cls,
                    handler.handler,
                    after=handler.after,
                ),
                *handler.filters,
            )
            used_observers.add(handler.name)

        for observer in used_observers:
            router.observers[observer].filter(StateFilter(scene_config.state))

    @classmethod
    def as_router(cls) -> Router:
        router = Router(name=cls.__scene_config__.state)
        cls.add_to_router(router)
        return router

    @classmethod
    def as_handler(cls) -> CallbackType:
        async def enter_to_scene_handler(event: TelegramObject, scenes: ScenesManager) -> None:
            await scenes.enter(cls)

        return enter_to_scene_handler


class SceneWizard:
    def __init__(
        self,
        scene_config: SceneConfig,
        manager: ScenesManager,
        state: FSMContext,
        update_type: str,
        event: TelegramObject,
        data: Dict[str, Any],
    ):
        self.scene_config = scene_config
        self.manager = manager
        self.state = state
        self.update_type = update_type
        self.event = event
        self.data = data

        self.scene: Optional[Scene] = None

    async def enter(self, _with_history: bool = False, **kwargs: Any) -> None:
        loggers.scene.debug("Entering scene %r", self.scene_config.state)
        await self.state.set_state(self.scene_config.state)
        await self._on_action(SceneAction.enter, **kwargs)

    async def leave(self, **kwargs: Any) -> None:
        loggers.scene.debug("Leaving scene %r", self.scene_config.state)
        await self.manager.history.snapshot()
        await self._on_action(SceneAction.leave, **kwargs)

    async def exit(self, **kwargs: Any) -> None:
        loggers.scene.debug("Exiting scene %r", self.scene_config.state)
        await self.state.set_state(None)
        await self.manager.history.clear()
        await self._on_action(SceneAction.exit, **kwargs)
        await self.manager.enter(None, _check_active=False, _with_history=False, **kwargs)

    async def back(self, **kwargs: Any) -> None:
        loggers.scene.debug("Back to previous scene from scene %s", self.scene_config.state)
        await self.leave()
        await self.manager.history.rollback()
        new_scene = await self.manager.history.rollback()
        await self.manager.enter(new_scene, _check_active=False, _with_history=False, **kwargs)

    async def replay(self, event: TelegramObject) -> None:
        await self._on_action(SceneAction.enter, event=event)

    async def goto(self, scene: Union[Type[Scene], str], **kwargs: Any) -> None:
        await self.leave(**kwargs)
        await self.manager.enter(scene, _check_active=False, **kwargs)

    async def _on_action(self, action: SceneAction, **kwargs: Any) -> bool:
        if not self.scene:
            raise ValueError("Scene is not initialized")

        loggers.scene.debug("Call action %r in scene %r", action.name, self.scene_config.state)
        action_config = self.scene_config.actions.get(action, {})
        if not action_config:
            loggers.scene.debug(
                "Action %r not found in scene %r", action.name, self.scene_config.state
            )
            return False

        event_type = self.update_type
        if event_type not in action_config:
            loggers.scene.debug(
                "Action %r for event %r not found in scene %r",
                action.name,
                event_type,
                self.scene_config.state,
            )
            return False
        await action_config[event_type].call(self.scene, self.event, **{**self.data, **kwargs})
        return True

    async def set_data(self, data: Dict[str, Any]) -> None:
        await self.state.set_data(data=data)

    async def get_data(self) -> Dict[str, Any]:
        return await self.state.get_data()

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.state.update_data(data=kwargs)

    async def clear_data(self) -> None:
        await self.set_data({})


class ScenesManager:
    def __init__(
        self,
        registry: SceneRegistry,
        update_type: str,
        event: TelegramObject,
        state: FSMContext,
        data: dict[str, Any],
    ) -> None:
        self.registry = registry
        self.update_type = update_type
        self.event = event
        self.state = state
        self.data = data

        self.history = HistoryManager(self.state)

    async def _get_scene(self, scene_type: Optional[Union[Type[Scene], str]]) -> Scene:
        scene_type = self.registry.get(scene_type)
        return scene_type(
            wizard=SceneWizard(
                scene_config=scene_type.__scene_config__,
                manager=self,
                state=self.state,
                update_type=self.update_type,
                event=self.event,
                data=self.data,
            ),
        )

    async def _get_active_scene(self) -> Optional[Scene]:
        state = await self.state.get_state()
        return await self._get_scene(state)

    async def enter(
        self,
        scene_type: Optional[Union[Type[Scene], str]],
        _check_active: bool = True,
        _with_history: bool = True,
        **kwargs: Any,
    ) -> None:
        scene = await self._get_scene(scene_type)
        if _check_active:
            active_scene = await self._get_active_scene()
            if active_scene is not None:
                await active_scene.wizard.exit(**kwargs)

        await scene.wizard.enter(_with_history=_with_history, **kwargs)

    async def close(self, **kwargs: Any) -> None:
        try:
            scene = await self._get_active_scene()
        except ValueError:
            return
        if not scene:
            return
        await scene.wizard.exit(**kwargs)


class SceneRegistry:
    def __init__(self, router: Router) -> None:
        self.router = router

        for observer in router.observers.values():
            if observer.event_name in {"update", "error"}:
                continue
            observer.outer_middleware(self._middleware)

        self._scenes: Dict[Optional[str], Type[Scene]] = {}

    async def _middleware(
        self,
        handler: NextMiddlewareType[TelegramObject],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        update: Update = data["event_update"]
        data["scenes"] = ScenesManager(
            registry=self,
            update_type=update.event_type,
            event=event,
            state=data["state"],
            data=data,
        )
        return await handler(event, data)

    def add(self, *scenes: Type[Scene], router: Optional[Router] = None) -> None:
        if router is None:
            router = self.router

        for scene in scenes:
            if scene.__scene_config__.state in self._scenes:
                raise ValueError(f"Scene {scene.__scene_config__.state} already exists")

            self._scenes[scene.__scene_config__.state] = scene

            router.include_router(scene.as_router())

    def get(self, scene: Optional[Union[Type[Scene], str]]) -> Type[Scene]:
        if inspect.isclass(scene) and issubclass(scene, Scene):
            scene = scene.__scene_config__.state
        if scene is not None and not isinstance(scene, str):
            raise TypeError("Scene must be a subclass of Scene or a string")

        try:
            result = self._scenes[scene]
        except KeyError:
            raise ValueError(f"Scene {scene!r} is not registered")

        return result


@dataclass
class After:
    action: SceneAction
    scene: Optional[Union[Type[Scene], str]] = None

    @classmethod
    def exit(cls) -> After:
        return cls(action=SceneAction.exit)

    @classmethod
    def back(cls) -> After:
        return cls(action=SceneAction.back)

    @classmethod
    def goto(cls, scene: Optional[Union[Type[Scene], str]]) -> After:
        return cls(action=SceneAction.enter, scene=scene)


class ObserverMarker:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(
        self,
        *filters: CallbackType,
        after: Optional[After] = None,
    ) -> ObserverDecorator:
        return ObserverDecorator(
            self.name,
            filters,
            after=after,
        )

    def enter(self, *filters: CallbackType) -> ObserverDecorator:
        return ObserverDecorator(self.name, filters, action=SceneAction.enter)

    def leave(self) -> ObserverDecorator:
        return ObserverDecorator(self.name, (), action=SceneAction.leave)

    def exit(self) -> ObserverDecorator:
        return ObserverDecorator(self.name, (), action=SceneAction.exit)

    def back(self) -> ObserverDecorator:
        return ObserverDecorator(self.name, (), action=SceneAction.back)


class OnMarker:
    """
    The `_On` class is used as a marker class to define different types of events in the Scenes.

    Attributes:

    - :code:`message`: Event marker for handling `Message` events.
    - :code:`edited_message`: Event marker for handling edited `Message` events.
    - :code:`channel_post`: Event marker for handling channel `Post` events.
    - :code:`edited_channel_post`: Event marker for handling edited channel `Post` events.
    - :code:`inline_query`: Event marker for handling `InlineQuery` events.
    - :code:`chosen_inline_result`: Event marker for handling chosen `InlineResult` events.
    - :code:`callback_query`: Event marker for handling `CallbackQuery` events.
    - :code:`shipping_query`: Event marker for handling `ShippingQuery` events.
    - :code:`pre_checkout_query`: Event marker for handling `PreCheckoutQuery` events.
    - :code:`poll`: Event marker for handling `Poll` events.
    - :code:`poll_answer`: Event marker for handling `PollAnswer` events.
    - :code:`my_chat_member`: Event marker for handling my chat `Member` events.
    - :code:`chat_member`: Event marker for handling chat `Member` events.
    - :code:`chat_join_request`: Event marker for handling chat `JoinRequest` events.
    - :code:`error`: Event marker for handling `Error` events.

    .. note::

        This is a marker class and does not contain any methods or implementation logic.
    """

    message = ObserverMarker("message")
    edited_message = ObserverMarker("edited_message")
    channel_post = ObserverMarker("channel_post")
    edited_channel_post = ObserverMarker("edited_channel_post")
    inline_query = ObserverMarker("inline_query")
    chosen_inline_result = ObserverMarker("chosen_inline_result")
    callback_query = ObserverMarker("callback_query")
    shipping_query = ObserverMarker("shipping_query")
    pre_checkout_query = ObserverMarker("pre_checkout_query")
    poll = ObserverMarker("poll")
    poll_answer = ObserverMarker("poll_answer")
    my_chat_member = ObserverMarker("my_chat_member")
    chat_member = ObserverMarker("chat_member")
    chat_join_request = ObserverMarker("chat_join_request")
