from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .base import TelegramMethod


class UnpinChatMessage(TelegramMethod[bool]):
    """
    Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#unpinchatmessage
    """

    __returning__ = bool
    __api_method__ = "unpinChatMessage"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    business_connection_id: Optional[str] = None
    """Unique identifier of the business connection on behalf of which the message will be unpinned"""
    message_id: Optional[int] = None
    """Identifier of the message to unpin. Required if *business_connection_id* is specified. If not specified, the most recent pinned message (by sending date) will be unpinned."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Union[int, str],
            business_connection_id: Optional[str] = None,
            message_id: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                message_id=message_id,
                **__pydantic_kwargs,
            )
