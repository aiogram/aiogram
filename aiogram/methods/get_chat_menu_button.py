from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import MenuButtonCommands, MenuButtonDefault, MenuButtonWebApp
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetChatMenuButton(
    TelegramMethod[Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]]
):
    """
    Use this method to get the current value of the bot's menu button in a private chat, or the default menu button. Returns :class:`aiogram.types.menu_button.MenuButton` on success.

    Source: https://core.telegram.org/bots/api#getchatmenubutton
    """

    __returning__ = Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]

    chat_id: Optional[int] = None
    """Unique identifier for the target private chat. If not specified, default bot's menu button will be returned"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getChatMenuButton", data=data)
