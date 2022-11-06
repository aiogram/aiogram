from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import MenuButtonCommands, MenuButtonDefault, MenuButtonWebApp
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetChatMenuButton(TelegramMethod[bool]):
    """
    Use this method to change the bot's menu button in a private chat, or the default menu button. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setchatmenubutton
    """

    __returning__ = bool

    chat_id: Optional[int] = None
    """Unique identifier for the target private chat. If not specified, default bot's menu button will be changed"""
    menu_button: Optional[Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]] = None
    """A JSON-serialized object for the bot's new menu button. Defaults to :class:`aiogram.types.menu_button_default.MenuButtonDefault`"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setChatMenuButton", data=data)
