from . import Deserializable


class VideoNote(Deserializable):
    __slots__ = ('file_id', 'length', 'duration', 'thumb', 'file_size')

    def __init__(self, file_id, length, duration, thumb, file_size):
        self.file_id = file_id
        self.length = length
        self.duration = duration
        self.thumb = thumb
        self.file_size = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        length = raw_data.get('length')
        duration = raw_data.get('duration')
        thumb = raw_data.get('thumb')
        file_size = raw_data.get('file_size')

        return VideoNote(file_id, length, duration, thumb, file_size)
