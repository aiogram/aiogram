from __future__ import annotations

import inspect
from collections import defaultdict
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, Tuple, Type, Union, Optional

from typing_extensions import Self

from aiogram.dispatcher.event.handler import CallableObject, CallbackType
from aiogram.types import TelegramObject

if TYPE_CHECKING:
    from ._scene import Scene


class ObserverMarker:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(
        self,
        *filters: CallbackType,
    ) -> ObserverDecorator:
        return ObserverDecorator(
            self.name,
            filters,
        )

    def enter(self, *filters: CallbackType) -> ObserverDecorator:
        return ObserverDecorator(self.name, filters, action=SceneAction.enter)

    def leave(self) -> ObserverDecorator:
        return ObserverDecorator(self.name, (), action=SceneAction.leave)

    def exit(self) -> ObserverDecorator:
        return ObserverDecorator(self.name, (), action=SceneAction.exit)

    def back(self) -> ObserverDecorator:
        return ObserverDecorator(self.name, (), action=SceneAction.back)


class ObserverDecorator:
    def __init__(
        self,
        name: str,
        filters: tuple[CallbackType, ...],
        action: SceneAction | None = None,
    ) -> None:
        self.name = name
        self.filters = filters
        self.action = action

    def _wrap_class(self, target: Type[Scene]) -> None:
        from ._scene import Scene

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
        setattr(target, "__aiogram_handler__", True)

        filters = getattr(target, "__aiogram_filters__", None)
        if filters is None:
            filters = defaultdict(list)
            setattr(target, "__aiogram_filters__", filters)
        filters[self.name].extend(self.filters)

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

    async def __call__(
        self,
        scene: Scene,
        event: TelegramObject,
    ) -> None:
        if self.action == SceneAction.enter and self.target is not None:
            await scene.goto(self.target)
        elif self.action == SceneAction.leave:
            await scene.leave()
        elif self.action == SceneAction.exit:
            await scene.exit()
        elif self.action == SceneAction.back:
            await scene.back()

    @property
    def __aiogram_filters__(self) -> Dict[str, Tuple[CallbackType, ...]]:
        return {self.name: self.filters}

    def __await__(self) -> Self:
        return self


class ControlActionContainer:
    def __init__(self, name: str, action: SceneAction) -> None:
        self.name = name
        self.action = action


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
