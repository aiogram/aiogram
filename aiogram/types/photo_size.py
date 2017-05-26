from . import Deserializable


class PhotoSize(Deserializable):
    __slots__ = ('file_id', 'width', 'height', 'file_size')

    def __init__(self, file_id, width, height, file_size):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.file_size = file_size

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        width = data.get('width')
        height = data.get('height')
        file_size = data.get('file_size')

        return PhotoSize(file_id, width, height, file_size)
