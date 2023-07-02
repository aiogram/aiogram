from __future__ import annotations

from typing import Literal

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllChatAdministrators(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chat administrators.

    Source: https://core.telegram.org/bots/api#botcommandscopeallchatadministrators
    """

    type: Literal[
        BotCommandScopeType.ALL_CHAT_ADMINISTRATORS
    ] = BotCommandScopeType.ALL_CHAT_ADMINISTRATORS
    """Scope type, must be *all_chat_administrators*"""
