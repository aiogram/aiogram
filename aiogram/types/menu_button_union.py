from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .menu_button_commands import MenuButtonCommands
from .menu_button_default import MenuButtonDefault
from .menu_button_web_app import MenuButtonWebApp

MenuButtonUnion: TypeAlias = Annotated[
    MenuButtonCommands | MenuButtonWebApp | MenuButtonDefault, Field(discriminator="type")
]
