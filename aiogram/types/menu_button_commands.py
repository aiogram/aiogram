from __future__ import annotations

from typing import Literal

from ..enums import MenuButtonType
from .menu_button import MenuButton


class MenuButtonCommands(MenuButton):
    """
    Represents a menu button, which opens the bot's list of commands.

    Source: https://core.telegram.org/bots/api#menubuttoncommands
    """

    type: Literal[MenuButtonType.COMMANDS] = MenuButtonType.COMMANDS
    """Type of the button, must be *commands*"""
