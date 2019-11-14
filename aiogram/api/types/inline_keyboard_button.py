from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .login_url import LoginUrl
    from .callback_game import CallbackGame


class InlineKeyboardButton(TelegramObject):
    """
    This object represents one button of an inline keyboard. You must use exactly one of the optional fields.

    Source: https://core.telegram.org/bots/api#inlinekeyboardbutton
    """

    text: str
    """Label text on the button"""
    url: Optional[str] = None
    """HTTP or tg:// url to be opened when button is pressed"""
    login_url: Optional[LoginUrl] = None
    """An HTTP URL used to automatically authorize the user. Can be used as a replacement for the Telegram Login Widget."""
    callback_data: Optional[str] = None
    """Data to be sent in a callback query to the bot when button is pressed, 1-64 bytes"""
    switch_inline_query: Optional[str] = None
    """If set, pressing the button will prompt the user to select one of their chats, open that chat and insert the bot‘s username and the specified inline query in the input field. Can be empty, in which case just the bot’s username will be inserted.

    Note: This offers an easy way for users to start using your bot in inline mode when they are currently in a private chat with it. Especially useful when combined with switch_pm… actions – in this case the user will be automatically returned to the chat they switched from, skipping the chat selection screen."""
    switch_inline_query_current_chat: Optional[str] = None
    """If set, pressing the button will insert the bot‘s username and the specified inline query in the current chat's input field. Can be empty, in which case only the bot’s username will be inserted.

    This offers a quick way for the user to open your bot in inline mode in the same chat – good for selecting something from multiple options."""
    callback_game: Optional[CallbackGame] = None
    """Description of the game that will be launched when the user presses the button.

    NOTE: This type of button must always be the first button in the first row."""
    pay: Optional[bool] = None
    """Specify True, to send a Pay button.

    NOTE: This type of button must always be the first button in the first row."""
