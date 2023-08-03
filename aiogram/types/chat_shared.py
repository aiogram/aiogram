from typing import TYPE_CHECKING, Any

from aiogram.types import TelegramObject


class ChatShared(TelegramObject):
    """
    This object contains information about the chat whose identifier was shared with the bot using a :class:`aiogram.types.keyboard_button_request_chat.KeyboardButtonRequestChat` button.

    Source: https://core.telegram.org/bots/api#chatshared
    """

    request_id: int
    """Identifier of the request"""
    chat_id: int
    """Identifier of the shared chat. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier. The bot may not have access to the chat and could be unable to use this identifier, unless the chat is already known to the bot by some other means."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, request_id: int, chat_id: int, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(request_id=request_id, chat_id=chat_id, **__pydantic_kwargs)
