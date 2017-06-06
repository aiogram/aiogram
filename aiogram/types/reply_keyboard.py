from .base import Serializable


class ReplyKeyboardMarkup(Serializable):
    """
    This object represents a custom keyboard with reply options
    
    https://core.telegram.org/bots/api#replykeyboardmarkup
    """
    def __init__(self, resize_keyboard=None, one_time_keyboard=None, selective=None, row_width=3):
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
        self.row_width = row_width

        self.keyboard = []

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

    def to_json(self):
        return {key: value for key, value in self.__dict__.items() if value and key != 'row_width'}


class KeyboardButton(Serializable):
    """
    This object represents one button of the reply keyboard. 
    
    For simple text buttons String can be used instead of this object to specify text of the button. 
    
    Optional fields are mutually exclusive
    
    https://core.telegram.org/bots/api#keyboardbutton
    """
    def __init__(self, text, request_contact=None, request_location=None):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location

    def to_json(self):
        return self.__dict__


class ReplyKeyboardRemove(Serializable):
    """
    Upon receiving a message with this object, 
    Telegram clients will remove the current custom keyboard and display the default letter-keyboard. 

    By default, custom keyboards are displayed until a new keyboard 
    is sent by a bot. 

    An exception is made for one-time keyboards that are hidden immediately after the user presses a button

    https://core.telegram.org/bots/api#replykeyboardremove
    """
    def __init__(self, selective=None):
        self.selective = selective

    def to_json(self):
        json_dict = {'remove_keyboard': True}
        if self.selective:
            json_dict['selective'] = True
        return json_dict
