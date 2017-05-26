from . import Deserializable


class Contact(Deserializable):
    __slots__ = ('data', 'phone_number', 'first_name', 'last_name', 'user_id')

    def __init__(self, data, phone_number, first_name, last_name, user_id):
        self.data = data
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        phone_number = data.get('phone_number')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        user_id = data.get('user_id')

        return Contact(data, phone_number, first_name, last_name, user_id)
