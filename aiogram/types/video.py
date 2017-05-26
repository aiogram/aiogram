from . import Deserializable


class Video(Deserializable):
    __slots__ = ('data', 'file_id', 'width', 'height', 'duration', 'thumb', 'mime_type', 'file_size')

    def __init__(self, data, file_id, width, height, duration, thumb, mime_type, file_size):
        self.data = data
        self.file_id = file_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = thumb
        self.mime_type = mime_type
        self.file_size = file_size

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        width = data.get('width')
        height = data.get('height')
        duration = data.get('duration')
        thumb = data.get('thumb')
        mime_type = data.get('mime_type')
        file_size = data.get('file_size')

        return Video(data, file_id, width, height, duration, thumb, mime_type, file_size)
