from __future__ import annotations

from typing import Literal

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllPrivateChats(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all private chats.

    Source: https://core.telegram.org/bots/api#botcommandscopeallprivatechats
    """

    type: Literal[BotCommandScopeType.ALL_PRIVATE_CHATS] = BotCommandScopeType.ALL_PRIVATE_CHATS
    """Scope type, must be *all_private_chats*"""
