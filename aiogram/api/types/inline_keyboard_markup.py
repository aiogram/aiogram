from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import MutableTelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .inline_keyboard_button import InlineKeyboardButton


class InlineKeyboardMarkup(MutableTelegramObject):
    """
    This object represents an inline keyboard that appears right next to the message it belongs
    to.
    Note: This will only work in Telegram versions released after 9 April, 2016. Older clients
    will display unsupported message.

    Source: https://core.telegram.org/bots/api#inlinekeyboardmarkup
    """

    inline_keyboard: List[List[InlineKeyboardButton]] = list()
    """Array of button rows, each represented by an Array of InlineKeyboardButton objects"""

    row_width: int = 3
    """Wight of row. New buttons will fit this limit."""

    def add(self, *args: InlineKeyboardButton) -> InlineKeyboardMarkup:
        """
        Add buttons

        :param args:
        :return: self
        """
        row = []
        for index, button in enumerate(args, start=1):
            row.append(button)
            if index % self.row_width == 0:
                self.inline_keyboard.append(row)
                row = []
        if len(row) > 0:
            self.inline_keyboard.append(row)
        return self

    def row(self, *args: InlineKeyboardButton) -> InlineKeyboardMarkup:
        """
        Add row

        :param args:
        :return: self
        """
        btn_array = []
        for button in args:
            btn_array.append(button)
        self.inline_keyboard.append(btn_array)
        return self

    def insert(self, button: InlineKeyboardButton) -> InlineKeyboardMarkup:
        """
        Insert button to last row

        :param button:
        :return: self
        """
        if self.inline_keyboard and len(self.inline_keyboard[-1]) < self.row_width:
            self.inline_keyboard[-1].append(button)
        else:
            self.add(button)
        return self
