from . import Deserializable


class VideoNote(Deserializable):
    __slots__ = ('data', 'file_id', 'length', 'duration', 'thumb', 'file_size')

    def __init__(self, data, file_id, length, duration, thumb, file_size):
        self.data = data
        self.file_id = file_id
        self.length = length
        self.duration = duration
        self.thumb = thumb
        self.file_size = file_size

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        length = data.get('length')
        duration = data.get('duration')
        thumb = data.get('thumb')
        file_size = data.get('file_size')

        return VideoNote(data, file_id, length, duration, thumb, file_size)
