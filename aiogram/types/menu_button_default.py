from __future__ import annotations

from pydantic import Field

from .menu_button import MenuButton


class MenuButtonDefault(MenuButton):
    """
    Describes that no specific value for the menu button was set.

    Source: https://core.telegram.org/bots/api#menubuttondefault
    """

    type: str = Field("default", const=True)
    """Type of the button, must be *default*"""
