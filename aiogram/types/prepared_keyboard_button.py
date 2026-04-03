from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class PreparedKeyboardButton(TelegramObject):
    """
    This object represents a prepared keyboard button that allows bots to request users, chats, and managed bots from Mini Apps.

    Source: https://core.telegram.org/bots/api#preparedkeyboardbutton
    """

    id: str
    """Unique identifier of the prepared button"""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                id=id,
                **__pydantic_kwargs,
            )
