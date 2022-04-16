from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from . import MenuButton

if TYPE_CHECKING:
    pass


class MenuButtonDefault(MenuButton):
    """
    Describes that no specific value for the menu button was set.

    Source: https://core.telegram.org/bots/api#menubuttondefault
    """

    type: str = Field("default", const=True)
    """Type of the button, must be *default*"""
