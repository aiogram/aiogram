from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class ManagedBotCreated(TelegramObject):
    """
    This object represents a service message about a bot created to be managed by the current bot.

    Source: https://core.telegram.org/bots/api#managedbotcreated
    """

    managed_bot: User = Field(alias="bot")
    """Information about the bot. The bot's token can be fetched using the method getManagedBotToken."""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            bot: User,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                bot=bot,
                **__pydantic_kwargs,
            )
