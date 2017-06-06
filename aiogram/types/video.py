from .base import Deserializable
from .photo_size import PhotoSize


class Video(Deserializable):
    """
    This object represents a video file.
    
    https://core.telegram.org/bots/api#video
    """
    def __init__(self, file_id, width, height, duration, thumb, mime_type, file_size):
        self.file_id: str = file_id
        self.width: int = width
        self.height: int = height
        self.duration: int = duration
        self.thumb: PhotoSize = thumb
        self.mime_type = mime_type
        self.file_size: int = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        width = raw_data.get('width')
        height = raw_data.get('height')
        duration = raw_data.get('duration')
        thumb = PhotoSize.deserialize(raw_data.get('thumb'))
        mime_type = raw_data.get('mime_type')
        file_size = raw_data.get('file_size')

        return Video(file_id, width, height, duration, thumb, mime_type, file_size)
