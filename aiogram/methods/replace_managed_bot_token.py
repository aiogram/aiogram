from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramMethod


class ReplaceManagedBotToken(TelegramMethod[str]):
    """
    Use this method to revoke the current token of a managed bot and generate a new one. Returns the new token as *String* on success.

    Source: https://core.telegram.org/bots/api#replacemanagedbottoken
    """

    __returning__ = str
    __api_method__ = "replaceManagedBotToken"

    user_id: int
    """User identifier of the managed bot whose token will be replaced"""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            user_id: int,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                user_id=user_id,
                **__pydantic_kwargs,
            )
