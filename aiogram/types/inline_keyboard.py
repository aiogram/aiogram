import typing

from . import base
from . import fields
from .callback_game import CallbackGame
from .login_url import LoginUrl


class InlineKeyboardMarkup(base.TelegramObject):
    """
    This object represents an inline keyboard that appears right next to the message it belongs to.

    Note: This will only work in Telegram versions released after 9 April, 2016.
    Older clients will display unsupported message.

    https://core.telegram.org/bots/api#inlinekeyboardmarkup
    """
    inline_keyboard: 'typing.List[typing.List[InlineKeyboardButton]]' = fields.ListOfLists(base='InlineKeyboardButton')

    def __init__(self, row_width=3, inline_keyboard=None, **kwargs):
        if inline_keyboard is None:
            inline_keyboard = []

        conf = kwargs.pop('conf', {}) or {}
        conf['row_width'] = row_width

        super(InlineKeyboardMarkup, self).__init__(**kwargs,
                                                   conf=conf,
                                                   inline_keyboard=inline_keyboard)

    @property
    def row_width(self):
        return self.conf.get('row_width', 3)

    @row_width.setter
    def row_width(self, value):
        self.conf['row_width'] = value

    def add(self, *args):
        """
        Add buttons

        :param args:
        :return: self
        :rtype: :obj:`types.InlineKeyboardMarkup`
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

    def row(self, *args):
        """
        Add row

        :param args:
        :return: self
        :rtype: :obj:`types.InlineKeyboardMarkup`
        """
        btn_array = []
        for button in args:
            btn_array.append(button)
        self.inline_keyboard.append(btn_array)
        return self

    def insert(self, button):
        """
        Insert button to last row

        :param button:
        :return: self
        :rtype: :obj:`types.InlineKeyboardMarkup`
        """
        if self.inline_keyboard and len(self.inline_keyboard[-1]) < self.row_width:
            self.inline_keyboard[-1].append(button)
        else:
            self.add(button)
        return self


class InlineKeyboardButton(base.TelegramObject):
    """
    This object represents one button of an inline keyboard. You must use exactly one of the optional fields.

    https://core.telegram.org/bots/api#inlinekeyboardbutton
    """
    text: base.String = fields.Field()
    url: base.String = fields.Field()
    login_url: LoginUrl = fields.Field(base=LoginUrl)
    callback_data: base.String = fields.Field()
    switch_inline_query: base.String = fields.Field()
    switch_inline_query_current_chat: base.String = fields.Field()
    callback_game: CallbackGame = fields.Field(base=CallbackGame)
    pay: base.Boolean = fields.Field()

    def __init__(self, text: base.String,
                 url: base.String = None,
                 login_url: LoginUrl = None,
                 callback_data: base.String = None,
                 switch_inline_query: base.String = None,
                 switch_inline_query_current_chat: base.String = None,
                 callback_game: CallbackGame = None,
                 pay: base.Boolean = None, **kwargs):
        super(InlineKeyboardButton, self).__init__(text=text,
                                                   url=url,
                                                   login_url=login_url,
                                                   callback_data=callback_data,
                                                   switch_inline_query=switch_inline_query,
                                                   switch_inline_query_current_chat=switch_inline_query_current_chat,
                                                   callback_game=callback_game,
                                                   pay=pay, **kwargs)
