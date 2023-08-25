from __future__ import annotations

from typing import Union, Optional

from aiogram.dispatcher.event.handler import CallbackType
from ._scene import Scene, ObserverDecorator, SceneAction


class ObserverMarker:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(
        self,
        *filters: CallbackType,
        goto: Optional[Union[Scene, str]] = None,
        exit_: bool = False,
        leave: bool = False,
        back: bool = False,
    ) -> ObserverDecorator:
        # Check that only one action is specified
        if sum((goto is not None, exit_, leave, back)) > 1:
            raise ValueError("Only one action is allowed")

        scene = None
        action_after = None
        if goto is not None:
            action_after = SceneAction.enter
            scene = goto
        elif exit_:
            action_after = SceneAction.exit
        elif leave:
            action_after = SceneAction.leave
        elif back:
            action_after = SceneAction.back

        return ObserverDecorator(
            self.name,
            filters,
            action_after=action_after,
            scene=scene,
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
