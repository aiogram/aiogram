from __future__ import annotations

from typing import Union

from pydantic import Field

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeChatMember(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering a specific member of a group or supergroup chat.

    Source: https://core.telegram.org/bots/api#botcommandscopechatmember
    """

    type: str = Field(BotCommandScopeType.CHAT_MEMBER, const=True)
    """Scope type, must be *chat_member*"""
    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
    user_id: int
    """Unique identifier of the target user"""
