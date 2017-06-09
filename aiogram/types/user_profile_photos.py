from .base import Deserializable
from .photo_size import PhotoSize


class UserProfilePhotos(Deserializable):
    """
    This object represent a user's profile pictures.
    
    https://core.telegram.org/bots/api#userprofilephotos
    """
    def __init__(self, total_count, photos):
        self.total_count: int = total_count
        self.photos: [PhotoSize] = photos

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        total_count = raw_data.get('total_count')
        photos = [PhotoSize.deserialize(item) for item in raw_data.get('photos')]

        return UserProfilePhotos(total_count, photos)
