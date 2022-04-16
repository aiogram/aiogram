from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from . import MenuButton

if TYPE_CHECKING:
    pass


class MenuButtonCommands(MenuButton):
    """
    Represents a menu button, which opens the bot's list of commands.

    Source: https://core.telegram.org/bots/api#menubuttoncommands
    """

    type: str = Field("commands", const=True)
    """Type of the button, must be *commands*"""
