from . import Deserializable


class UserProfilePhotos(Deserializable):
    __slots__ = ('total_count', 'photos')

    def __init__(self, total_count, photos):
        self.total_count = total_count
        self.photos = photos

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        total_count = raw_data.get('total_count')
        photos = raw_data.get('photos')

        return UserProfilePhotos(total_count, photos)
