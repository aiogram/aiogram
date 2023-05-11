from __future__ import annotations

import msgspec

from ..enums import MenuButtonType
from .menu_button import MenuButton


class MenuButtonDefault(MenuButton):
    """
    Describes that no specific value for the menu button was set.

    Source: https://core.telegram.org/bots/api#menubuttondefault
    """

    type: str = msgspec.field(default_factory=lambda: MenuButtonType.DEFAULT)
    """Type of the button, must be *default*"""
