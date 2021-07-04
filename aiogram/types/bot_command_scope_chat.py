from __future__ import annotations

from typing import Union

from pydantic import Field

from .bot_command_scope import BotCommandScope


class BotCommandScopeChat(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering a specific chat.

    Source: https://core.telegram.org/bots/api#botcommandscopechat
    """

    type: str = Field("chat", const=True)
    """Scope type, must be *chat*"""
    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
