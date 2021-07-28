from __future__ import annotations

from pydantic import Field

from .bot_command_scope import BotCommandScope


class BotCommandScopeAllChatAdministrators(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all group and supergroup chat administrators.

    Source: https://core.telegram.org/bots/api#botcommandscopeallchatadministrators
    """

    type: str = Field("all_chat_administrators", const=True)
    """Scope type, must be *all_chat_administrators*"""
