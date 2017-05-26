from . import Deserializable


class File(Deserializable):
    __slots__ = ('data', 'file_id', 'file_size', 'file_path')

    def __init__(self, data, file_id, file_size, file_path):
        self.data = data
        self.file_id = file_id
        self.file_size = file_size
        self.file_path = file_path

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        file_size = data.get('file_size')
        file_path = data.get('file_path')

        return File(data, file_id, file_size, file_path)
