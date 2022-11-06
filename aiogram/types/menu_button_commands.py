from __future__ import annotations

from pydantic import Field

from .menu_button import MenuButton


class MenuButtonCommands(MenuButton):
    """
    Represents a menu button, which opens the bot's list of commands.

    Source: https://core.telegram.org/bots/api#menubuttoncommands
    """

    type: str = Field("commands", const=True)
    """Type of the button, must be *commands*"""
