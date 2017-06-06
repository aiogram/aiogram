from .base import Deserializable
from .photo_size import PhotoSize


class Sticker(Deserializable):
    """
    This object represents a sticker.
    
    https://core.telegram.org/bots/api#sticker
    """
    def __init__(self, file_id, width, height, thumb, emoji, file_size):
        self.file_id: str = file_id
        self.width: int = width
        self.height: int = height
        self.thumb: PhotoSize = thumb
        self.emoji: str = emoji
        self.file_size: int = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        width = raw_data.get('width')
        height = raw_data.get('height')
        thumb = PhotoSize.deserialize(raw_data.get('thumb'))
        emoji = raw_data.get('emoji')
        file_size = raw_data.get('file_size')

        return Sticker(file_id, width, height, thumb, emoji, file_size)
