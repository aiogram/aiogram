from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class KeyboardButtonRequestManagedBot(TelegramObject):
    """
    This object defines the parameters for the creation of a managed bot. Information about the created bot will be shared with the bot using the update *managed_bot* and a :class:`aiogram.types.message.Message` with the field *managed_bot_created*.

    Source: https://core.telegram.org/bots/api#keyboardbuttonrequestmanagedbot
    """

    request_id: int
    """Signed 32-bit identifier of the request. Must be unique within the message"""
    suggested_name: str | None = None
    """*Optional*. Suggested name for the bot"""
    suggested_username: str | None = None
    """*Optional*. Suggested username for the bot"""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            request_id: int,
            suggested_name: str | None = None,
            suggested_username: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                request_id=request_id,
                suggested_name=suggested_name,
                suggested_username=suggested_username,
                **__pydantic_kwargs,
            )
