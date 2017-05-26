from . import Deserializable


class Document(Deserializable):
    __slots__ = ('file_id', 'thumb', 'file_name', 'mime_type', 'file_size')

    def __init__(self, file_id, thumb, file_name, mime_type, file_size):
        self.file_id = file_id
        self.thumb = thumb
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        thumb = raw_data.get('thumb')
        file_name = raw_data.get('file_name')
        mime_type = raw_data.get('mime_type')
        file_size = raw_data.get('file_size')

        return Document(file_id, thumb, file_name, mime_type, file_size)
