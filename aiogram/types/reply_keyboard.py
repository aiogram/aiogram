import typing

from . import base
from . import fields


class ReplyKeyboardMarkup(base.TelegramObject):
    """
    This object represents a custom keyboard with reply options (see Introduction to bots for details and examples).

    https://core.telegram.org/bots/api#replykeyboardmarkup
    """
    keyboard: 'typing.List[typing.List[KeyboardButton]]' = fields.ListOfLists(base='KeyboardButton', default=[])
    resize_keyboard: base.Boolean = fields.Field()
    one_time_keyboard: base.Boolean = fields.Field()
    selective: base.Boolean = fields.Field()

    def __init__(self, keyboard: 'typing.List[typing.List[KeyboardButton]]' = None,
                 resize_keyboard: base.Boolean = None,
                 one_time_keyboard: base.Boolean = None,
                 selective: base.Boolean = None,
                 row_width: base.Integer = 3):
        super(ReplyKeyboardMarkup, self).__init__(keyboard=keyboard, resize_keyboard=resize_keyboard,
                                                  one_time_keyboard=one_time_keyboard, selective=selective,
                                                  conf={'row_width': row_width})

    @property
    def row_width(self):
        return self.conf.get('row_width', 3)

    @row_width.setter
    def row_width(self, value):
        self.conf['row_width'] = value

    def add(self, *args):
        i = 1
        row = []
        for button in args:
            if isinstance(button, str):
                row.append({'text': button})
            elif isinstance(button, bytes):
                row.append({'text': button.decode('utf-8')})
            else:
                row.append(button.to_json())
            if i % self.row_width == 0:
                self.keyboard.append(row)
                row = []
            i += 1
        if len(row) > 0:
            self.keyboard.append(row)

    def row(self, *args):
        btn_array = []
        for button in args:
            if isinstance(button, str):
                btn_array.append({'text': button})
            else:
                btn_array.append(button.to_json())
        self.keyboard.append(btn_array)
        return self


class KeyboardButton(base.TelegramObject):
    """
    This object represents one button of the reply keyboard. For simple text buttons String can be used instead of this object to specify text of the button. Optional fields are mutually exclusive.
    Note: request_contact and request_location options will only work in Telegram versions released after 9 April, 2016. Older clients will ignore them.

    https://core.telegram.org/bots/api#keyboardbutton
    """
    text: base.String = fields.Field()
    request_contact: base.Boolean = fields.Field()
    request_location: base.Boolean = fields.Field()

    def __init__(self, text: base.String, request_contact: base.Boolean = None, request_location: base.Boolean = None):
        super(KeyboardButton, self).__init__(text=text, request_contact=request_contact,
                                             request_location=request_location)


class ReplyKeyboardRemove(base.TelegramObject):
    """
    Upon receiving a message with this object, Telegram clients will remove the current custom keyboard and display the default letter-keyboard. By default, custom keyboards are displayed until a new keyboard is sent by a bot. An exception is made for one-time keyboards that are hidden immediately after the user presses a button (see ReplyKeyboardMarkup).

    https://core.telegram.org/bots/api#replykeyboardremove
    """
    remove_keyboard: base.Boolean = fields.Field(default=True)
    selective: base.Boolean = fields.Field()

    def __init__(self, selective: base.Boolean = None):
        super(ReplyKeyboardRemove, self).__init__(remove_keyboard=True, selective=selective)
