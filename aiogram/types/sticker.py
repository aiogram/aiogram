from . import Deserializable


class Sticker(Deserializable):
    __slots__ = ('data', 'file_id', 'width', 'height', 'thumb', 'emoji', 'file_size')

    def __init__(self, data, file_id, width, height, thumb, emoji, file_size):
        self.data = data
        self.file_id = file_id
        self.width = width
        self.height = height
        self.thumb = thumb
        self.emoji = emoji
        self.file_size = file_size

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        file_id = data.get('file_id')
        width = data.get('width')
        height = data.get('height')
        thumb = data.get('thumb')
        emoji = data.get('emoji')
        file_size = data.get('file_size')

        return Sticker(data, file_id, width, height, thumb, emoji, file_size)
