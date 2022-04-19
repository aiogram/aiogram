from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramObject

if TYPE_CHECKING:
    pass


class MenuButton(TelegramObject):
    """
    This object describes the bot's menu button in a private chat. It should be one of

     - :class:`aiogram.types.menu_button_commands.MenuButtonCommands`
     - :class:`aiogram.types.menu_button_web_app.MenuButtonWebApp`
     - :class:`aiogram.types.menu_button_default.MenuButtonDefault`

    If a menu button other than :class:`aiogram.types.menu_button_default.MenuButtonDefault` is set for a private chat, then it is applied in the chat. Otherwise the default menu button is applied. By default, the menu button opens the list of bot commands.

    Source: https://core.telegram.org/bots/api#menubutton
    """
