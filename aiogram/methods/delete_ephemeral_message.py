from typing import TYPE_CHECKING, Any

from ..types import ChatIdUnion
from .base import TelegramMethod


class DeleteEphemeralMessage(TelegramMethod[bool]):
    """
    Use this method to delete an ephemeral message. Note that it is not guaranteed that the user will receive the message deletion event, especially if they are offline. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deleteephemeralmessage
    """

    __returning__ = bool
    __api_method__ = "deleteEphemeralMessage"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target supergroup in the format :code:`@username`"""
    receiver_user_id: int
    """Identifier of the user who received the message"""
    ephemeral_message_id: int
    """Identifier of the ephemeral message to delete"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            receiver_user_id: int,
            ephemeral_message_id: int,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                receiver_user_id=receiver_user_id,
                ephemeral_message_id=ephemeral_message_id,
                **__pydantic_kwargs,
            )
