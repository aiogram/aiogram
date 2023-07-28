from __future__ import annotations

from typing import List, Optional, Union

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


class SetMyCommands(TelegramMethod[bool]):
    """
    Use this method to change the list of the bot's commands. See `this manual <https://core.telegram.org/bots/features#commands>`_ for more details about bot commands. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setmycommands
    """

    __returning__ = bool
    __api_method__ = "setMyCommands"

    commands: List[BotCommand]
    """A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified."""
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
    """A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to :class:`aiogram.types.bot_command_scope_default.BotCommandScopeDefault`."""
    language_code: Optional[str] = None
    """A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands"""
