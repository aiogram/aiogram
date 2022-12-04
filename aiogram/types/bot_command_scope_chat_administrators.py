from __future__ import annotations

from typing import Union

from pydantic import Field

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeChatAdministrators(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all administrators of a specific group or supergroup chat.

    Source: https://core.telegram.org/bots/api#botcommandscopechatadministrators
    """

    type: str = Field(BotCommandScopeType.CHAT_ADMINISTRATORS, const=True)
    """Scope type, must be *chat_administrators*"""
    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
