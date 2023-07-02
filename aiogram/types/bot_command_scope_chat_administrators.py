from __future__ import annotations

from typing import Literal, Union

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeChatAdministrators(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering all administrators of a specific group or supergroup chat.

    Source: https://core.telegram.org/bots/api#botcommandscopechatadministrators
    """

    type: Literal[
        BotCommandScopeType.CHAT_ADMINISTRATORS
    ] = BotCommandScopeType.CHAT_ADMINISTRATORS
    """Scope type, must be *chat_administrators*"""
    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""
