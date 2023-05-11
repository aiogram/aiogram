from __future__ import annotations

import msgspec

from ..enums import MenuButtonType
from .menu_button import MenuButton


class MenuButtonCommands(MenuButton):
    """
    Represents a menu button, which opens the bot's list of commands.

    Source: https://core.telegram.org/bots/api#menubuttoncommands
    """

    type: str = msgspec.field(default_factory=lambda: MenuButtonType.COMMANDS)
    """Type of the button, must be *commands*"""
