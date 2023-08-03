from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..types import Chat
from .base import TelegramMethod


class GetChat(TelegramMethod[Chat]):
    """
    Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a :class:`aiogram.types.chat.Chat` object on success.

    Source: https://core.telegram.org/bots/api#getchat
    """

    __returning__ = Chat
    __api_method__ = "getChat"

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup or channel (in the format :code:`@channelusername`)"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, chat_id: Union[int, str], **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat_id=chat_id, **__pydantic_kwargs)
