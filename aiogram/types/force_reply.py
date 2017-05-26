from aiogram.types import Serializable


class ForceReply(Serializable):
    def __init__(self, selective=None):
        self.selective = selective

    def to_json(self):
        data = {'force_reply': True}
        if self.selective:
            data['selective'] = True
        return data
