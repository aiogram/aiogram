from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..types import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeChatAdministrators,
    BotCommandScopeChatMember,
    BotCommandScopeDefault,
)
from .base import TelegramMethod


class GetMyCommands(TelegramMethod[list[BotCommand]]):
    """
    Use this method to get the current list of the bot's commands for the given scope and user language. Returns an Array of :class:`aiogram.types.bot_command.BotCommand` objects. If commands aren't set, an empty list is returned.

    Source: https://core.telegram.org/bots/api#getmycommands
    """

    __returning__ = list[BotCommand]
    __api_method__ = "getMyCommands"

    scope: Optional[
        Union[
            BotCommandScopeDefault,
            BotCommandScopeAllPrivateChats,
            BotCommandScopeAllGroupChats,
            BotCommandScopeAllChatAdministrators,
            BotCommandScopeChat,
            BotCommandScopeChatAdministrators,
            BotCommandScopeChatMember,
        ]
    ] = None
    """A JSON-serialized object, describing scope of users. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code or an empty string"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            scope: Optional[
                Union[
                    BotCommandScopeDefault,
                    BotCommandScopeAllPrivateChats,
                    BotCommandScopeAllGroupChats,
                    BotCommandScopeAllChatAdministrators,
                    BotCommandScopeChat,
                    BotCommandScopeChatAdministrators,
                    BotCommandScopeChatMember,
                ]
            ] = None,
            language_code: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(scope=scope, language_code=language_code, **__pydantic_kwargs)
