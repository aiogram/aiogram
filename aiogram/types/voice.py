from . import Deserializable


class Voice(Deserializable):
    __slots__ = ('data', 'file_id', 'duration', 'mime_type', 'file_size')

    def __init__(self, data, file_id, duration, mime_type, file_size):
        self.data = data
        self.file_id = file_id
        self.duration = duration
        self.mime_type = mime_type
        self.file_size = file_size

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        duration = data.get('duration')
        mime_type = data.get('mime_type')
        file_size = data.get('file_size')

        return Voice(data, file_id, duration, mime_type, file_size)
