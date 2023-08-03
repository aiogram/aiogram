from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Union

from ..enums import BotCommandScopeType
from .bot_command_scope import BotCommandScope


class BotCommandScopeChat(BotCommandScope):
    """
    Represents the `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands, covering a specific chat.

    Source: https://core.telegram.org/bots/api#botcommandscopechat
    """

    type: Literal[BotCommandScopeType.CHAT] = BotCommandScopeType.CHAT
    """Scope type, must be *chat*"""
    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target supergroup (in the format :code:`@supergroupusername`)"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[BotCommandScopeType.CHAT] = BotCommandScopeType.CHAT,
            chat_id: Union[int, str],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, chat_id=chat_id, **__pydantic_kwargs)
