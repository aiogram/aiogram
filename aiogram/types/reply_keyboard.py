from . import Serializable


class ReplyKeyboardMarkup(Serializable):
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
    def __init__(self, text, request_contact=None, request_location=None):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location

    def to_json(self):
        return self.__dict__


class ReplyKeyboardRemove(Serializable):
    def __init__(self, selective=None):
        self.selective = selective

    def to_json(self):
        json_dict = {'remove_keyboard': True}
        if self.selective:
            json_dict['selective'] = True
        return json_dict
