from __future__ import annotations

from typing import Optional, Union

from ..types import MenuButtonCommands, MenuButtonDefault, MenuButtonWebApp
from .base import TelegramMethod


class SetChatMenuButton(TelegramMethod[bool]):
    """
    Use this method to change the bot's menu button in a private chat, or the default menu button. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatmenubutton
    """

    __returning__ = bool
    __api_method__ = "setChatMenuButton"

    chat_id: Optional[int] = None
    """Unique identifier for the target private chat. If not specified, default bot's menu button will be changed"""
    menu_button: Optional[Union[MenuButtonCommands, MenuButtonWebApp, MenuButtonDefault]] = None
    """A JSON-serialized object for the bot's new menu button. Defaults to :class:`aiogram.types.menu_button_default.MenuButtonDefault`"""
