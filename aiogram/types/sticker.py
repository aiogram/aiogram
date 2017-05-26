from . import Deserializable


class Sticker(Deserializable):
    def __init__(self, file_id, width, height, thumb, emoji, file_size):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.thumb = thumb
        self.emoji = emoji
        self.file_size = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        width = raw_data.get('width')
        height = raw_data.get('height')
        thumb = raw_data.get('thumb')
        emoji = raw_data.get('emoji')
        file_size = raw_data.get('file_size')

        return Sticker(file_id, width, height, thumb, emoji, file_size)
