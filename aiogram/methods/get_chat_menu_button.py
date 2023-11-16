from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..types import MenuButtonCommands, MenuButtonDefault, MenuButtonWebApp
from .base import TelegramMethod


class GetChatMenuButton(
    TelegramMethod[Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]]
):
    """
    Use this method to get the current value of the bot's menu button in a private chat, or the default menu button. Returns :class:`aiogram.types.menu_button.MenuButton` on success.

    Source: https://core.telegram.org/bots/api#getchatmenubutton
    """

    __returning__ = Union[MenuButtonDefault, MenuButtonWebApp, MenuButtonCommands]
    __api_method__ = "getChatMenuButton"

    chat_id: Optional[int] = None
    """Unique identifier for the target private chat. If not specified, default bot's menu button will be returned"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__, *, chat_id: Optional[int] = None, **__pydantic_kwargs: Any
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(chat_id=chat_id, **__pydantic_kwargs)
