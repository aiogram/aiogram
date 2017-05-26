from . import Deserializable


class Document(Deserializable):
    __slots__ = ('data', 'file_id', 'thumb', 'file_name', 'mime_type', 'file_size')

    def __init__(self, data, file_id, thumb, file_name, mime_type, file_size):
        self.data = data
        self.file_id = file_id
        self.thumb = thumb
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        thumb = data.get('thumb')
        file_name = data.get('file_name')
        mime_type = data.get('mime_type')
        file_size = data.get('file_size')

        return Document(data, file_id, thumb, file_name, mime_type, file_size)
