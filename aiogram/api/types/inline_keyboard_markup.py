from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramObject

if TYPE_CHECKING:
    from .inline_keyboard_button import InlineKeyboardButton


class InlineKeyboardMarkup(TelegramObject):
    """
    This object represents an inline keyboard that appears right next to the message it belongs to.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients will display unsupported message.

    Source: https://core.telegram.org/bots/api#inlinekeyboardmarkup
    """

    inline_keyboard: List[List[InlineKeyboardButton]]
    """Array of button rows, each represented by an Array of InlineKeyboardButton objects"""
