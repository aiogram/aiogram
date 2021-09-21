from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .base import MutableTelegramObject

if TYPE_CHECKING:
    from .keyboard_button import KeyboardButton


class ReplyKeyboardMarkup(MutableTelegramObject):
    """
    This object represents a `custom keyboard <https://core.telegram.org/bots#keyboards>`_ with reply options (see `Introduction to bots <https://core.telegram.org/bots#keyboards>`_ for details and examples).

    Source: https://core.telegram.org/bots/api#replykeyboardmarkup
    """

    keyboard: List[List[KeyboardButton]]
    """Array of button rows, each represented by an Array of :class:`aiogram.types.keyboard_button.KeyboardButton` objects"""
    resize_keyboard: Optional[bool] = None
    """*Optional*. Requests clients to resize the keyboard vertically for optimal fit (e.g., make the keyboard smaller if there are just two rows of buttons). Defaults to *false*, in which case the custom keyboard is always of the same height as the app's standard keyboard."""
    one_time_keyboard: Optional[bool] = None
    """*Optional*. Requests clients to hide the keyboard as soon as it's been used. The keyboard will still be available, but clients will automatically display the usual letter-keyboard in the chat – the user can press a special button in the input field to see the custom keyboard again. Defaults to *false*."""
    input_field_placeholder: Optional[str] = None
    """*Optional*. The placeholder to be shown in the input field when the keyboard is active; 1-64 characters"""
    selective: Optional[bool] = None
    """*Optional*. Use this parameter if you want to show the keyboard to specific users only. Targets: 1) users that are @mentioned in the *text* of the :class:`aiogram.types.message.Message` object; 2) if the bot's message is a reply (has *reply_to_message_id*), sender of the original message."""
