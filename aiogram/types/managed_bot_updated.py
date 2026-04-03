from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from .user import User


class ManagedBotUpdated(TelegramObject):
    """
    This object represents the creation or token update of a managed bot.

    Source: https://core.telegram.org/bots/api#managedbotupdated
    """

    user: User
    """The user who created or updated the managed bot"""
    managed_bot: User = Field(alias="bot")
    """Information about the managed bot. Token of the bot can be fetched using the method getManagedBotToken."""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            user: User,
            bot: User,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                user=user,
                bot=bot,
                **__pydantic_kwargs,
            )
