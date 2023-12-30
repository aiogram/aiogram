from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .maybe_inaccessible_message import MaybeInaccessibleMessage

if TYPE_CHECKING:
    from .chat import Chat


class InaccessibleMessage(MaybeInaccessibleMessage):
    """
    This object describes a message that was deleted or is otherwise inaccessible to the bot.

    Source: https://core.telegram.org/bots/api#inaccessiblemessage
    """

    chat: Chat
    """Chat the message belonged to"""
    message_id: int
    """Unique message identifier inside the chat"""
    date: Literal[0] = 0
    """Always 0. The field can be used to differentiate regular and inaccessible messages."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat: Chat,
            message_id: int,
            date: Literal[0] = 0,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat=chat, message_id=message_id, date=date, **__pydantic_kwargs)
