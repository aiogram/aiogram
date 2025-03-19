from __future__ import annotations

from typing import Union

from .menu_button_commands import MenuButtonCommands
from .menu_button_default import MenuButtonDefault
from .menu_button_web_app import MenuButtonWebApp

MenuButtonUnion = Union[MenuButtonCommands, MenuButtonWebApp, MenuButtonDefault]
