from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import MutableTelegramObject

if TYPE_CHECKING:
    from .callback_game import CallbackGame
    from .login_url import LoginUrl


class InlineKeyboardButton(MutableTelegramObject):
    """
    This object represents one button of an inline keyboard. You **must** use exactly one of the optional fields.

    Source: https://core.telegram.org/bots/api#inlinekeyboardbutton
    """

    text: str
    """Label text on the button"""
    url: Optional[str] = None
    """*Optional*. HTTP or tg:// url to be opened when the button is pressed. Links :code:`tg://user?id=<user_id>` can be used to mention a user by their ID without using a username, if this is allowed by their privacy settings."""
    login_url: Optional[LoginUrl] = None
    """*Optional*. An HTTP URL used to automatically authorize the user. Can be used as a replacement for the `Telegram Login Widget <https://core.telegram.org/widgets/login>`_."""
    callback_data: Optional[str] = None
    """*Optional*. Data to be sent in a `callback query <https://core.telegram.org/bots/api#callbackquery>`_ to the bot when button is pressed, 1-64 bytes"""
    switch_inline_query: Optional[str] = None
    """*Optional*. If set, pressing the button will prompt the user to select one of their chats, open that chat and insert the bot's username and the specified inline query in the input field. Can be empty, in which case just the bot's username will be inserted."""
    switch_inline_query_current_chat: Optional[str] = None
    """*Optional*. If set, pressing the button will insert the bot's username and the specified inline query in the current chat's input field. Can be empty, in which case only the bot's username will be inserted."""
    callback_game: Optional[CallbackGame] = None
    """*Optional*. Description of the game that will be launched when the user presses the button."""
    pay: Optional[bool] = None
    """*Optional*. Specify :code:`True`, to send a `Pay button <https://core.telegram.org/bots/api#payments>`_."""
