from . import Deserializable


class ChatMember(Deserializable):
    def __init__(self, user, status):
        self.user = user
        self.status = status

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        user = raw_data.get('user')
        status = raw_data.get('status')

        return ChatMember(user, status)
