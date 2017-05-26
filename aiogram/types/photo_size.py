from . import Deserializable


class PhotoSize(Deserializable):
    __slots__ = ('file_id', 'width', 'height', 'file_size')

    def __init__(self, file_id, width, height, file_size):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.file_size = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        width = raw_data.get('width')
        height = raw_data.get('height')
        file_size = raw_data.get('file_size')

        return PhotoSize(file_id, width, height, file_size)
