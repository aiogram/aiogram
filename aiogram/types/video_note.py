from .base import Deserializable
from .photo_size import PhotoSize


class VideoNote(Deserializable):
    """
    This object represents a video message.
    
    https://core.telegram.org/bots/api#videonote
    """
    def __init__(self, file_id, length, duration, thumb, file_size):
        self.file_id: str = file_id
        self.length: int = length
        self.duration: int = duration
        self.thumb: PhotoSize = thumb
        self.file_size: int = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        length = raw_data.get('length')
        duration = raw_data.get('duration')
        thumb = PhotoSize.deserialize(raw_data.get('thumb'))
        file_size = raw_data.get('file_size')

        return VideoNote(file_id, length, duration, thumb, file_size)
