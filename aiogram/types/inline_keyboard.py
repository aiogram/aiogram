from .base import Serializable


class InlineKeyboardMarkup(Serializable):
    """
    This object represents an inline keyboard that appears right next to the message it belongs to.
    
    https://core.telegram.org/bots/api#inlinekeyboardmarkup
    """
    def __init__(self, row_width=3):
        self.row_width = row_width

        self.keyboard = []

    def add(self, *args):
        i = 1
        row = []
        for button in args:
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
            btn_array.append(button.to_json())
        self.keyboard.append(btn_array)
        return self

    def to_json(self):
        return {'inline_keyboard': self.keyboard}


class InlineKeyboardButton(Serializable):
    """
    This object represents one button of an inline keyboard. You must use exactly one of the optional fields.
    
    https://core.telegram.org/bots/api#inlinekeyboardbutton
    """
    def __init__(self, text, url=None, callback_data=None, switch_inline_query=None,
                 switch_inline_query_current_chat=None, callback_game=None, pay=None):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        self.callback_game = callback_game
        self.pay = pay

    def to_json(self):
        return {key: value for key, value in self.__dict__.items() if value}
