from .base import deserialize, Deserializable


class PhotoSize(Deserializable):
    """
    This object represents one size of a photo or a file / sticker thumbnail.
    
    https://core.telegram.org/bots/api#photosize
    """
    def __init__(self, file_id, width, height, file_size):
        self.file_id: str = file_id
        self.width: int = width
        self.height: int = height
        self.file_size: int = file_size

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        width = raw_data.get('width')
        height = raw_data.get('height')
        file_size = raw_data.get('file_size')

        return PhotoSize(file_id, width, height, file_size)

    @classmethod
    def parse_array(cls, photos):
        return [deserialize(PhotoSize, photo) for photo in photos] if photos else None
