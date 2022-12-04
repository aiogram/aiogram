from __future__ import annotations

from pydantic import Field

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeAllChatAdministrators(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chat administrators.

    Source: https://core.telegram.org/bots/api#botcommandscopeallchatadministrators
    """

    type: str = Field(BotCommandScopeType.ALL_CHAT_ADMINISTRATORS, const=True)
    """Scope type, must be *all_chat_administrators*"""
