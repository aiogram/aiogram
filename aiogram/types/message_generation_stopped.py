from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .chat import Chat


class MessageGenerationStopped(TelegramObject):
    """
    This object describes an update about a user stopping message generation.

    Source: https://core.telegram.org/bots/api#messagegenerationstopped
    """

    chat: Chat
    """Chat in which the message is generated"""
    draft_id: int
    """Unique identifier of the message draft which was stopped"""
    message_thread_id: int | None = None
    """*Optional*. Unique identifier of the message thread in which the message is generated"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat: Chat,
            draft_id: int,
            message_thread_id: int | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat=chat,
                draft_id=draft_id,
                message_thread_id=message_thread_id,
                **__pydantic_kwargs,
            )
