from __future__ import annotations

from pydantic import Field

from .bot_command_scope import BotCommandScope


class BotCommandScopeDefault(BotCommandScope):
    """
    Represents the default `scope <https://core.telegram.org/bots/api#botcommandscope>`_ of bot commands. Default commands are used if no commands with a `narrower scope <https://core.telegram.org/bots/api#determining-list-of-commands>`_ are specified for the user.

    Source: https://core.telegram.org/bots/api#botcommandscopedefault
    """

    type: str = Field("default", const=True)
    """Scope type, must be *default*"""
