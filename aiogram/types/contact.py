from .base import Deserializable


class Contact(Deserializable):
    """
    This object represents a phone contact.
    
    https://core.telegram.org/bots/api#contact
    """
    def __init__(self, phone_number, first_name, last_name, user_id):
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.user_id: int = user_id

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        phone_number = raw_data.get('phone_number')
        first_name = raw_data.get('first_name')
        last_name = raw_data.get('last_name')
        user_id = raw_data.get('user_id')

        return Contact(phone_number, first_name, last_name, user_id)
