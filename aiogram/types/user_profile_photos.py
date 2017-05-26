from aiogram.types.photo_size import PhotoSize
from . import Deserializable


class UserProfilePhotos(Deserializable):
    def __init__(self, total_count, photos):
        self.total_count: int = total_count
        self.photos: [PhotoSize] = photos

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        total_count = raw_data.get('total_count')
        photos = PhotoSize.deserialize_array(raw_data.get('photos'))

        return UserProfilePhotos(total_count, photos)
