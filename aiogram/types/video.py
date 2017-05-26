from . import Deserializable


class Video(Deserializable):
    __slots__ = ('file_id', 'width', 'height', 'duration', 'thumb', 'mime_type', 'file_size')

    def __init__(self, file_id, width, height, duration, thumb, mime_type, file_size):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = thumb
        self.mime_type = mime_type
        self.file_size = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        width = raw_data.get('width')
        height = raw_data.get('height')
        duration = raw_data.get('duration')
        thumb = raw_data.get('thumb')
        mime_type = raw_data.get('mime_type')
        file_size = raw_data.get('file_size')

        return Video(file_id, width, height, duration, thumb, mime_type, file_size)
