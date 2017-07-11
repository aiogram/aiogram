from .base import Deserializable


class ChatPhoto(Deserializable):
    """
    This object represents a chat photo.
    
    https://core.telegram.org/bots/api#chatphoto
    """

    def __init__(self, small_file_id, big_file_id):
        self.small_file_id: str = small_file_id
        self.big_file_id: str = big_file_id

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        small_file_id = raw_data.get('small_file_id')
        big_file_id = raw_data.get('big_file_id')

        return ChatPhoto(small_file_id, big_file_id)
