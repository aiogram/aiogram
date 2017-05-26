from . import Deserializable


class UserProfilePhotos(Deserializable):
    __slots__ = ('data', 'total_count', 'photos')

    def __init__(self, data, total_count, photos):
        self.data = data
        self.total_count = total_count
        self.photos = photos

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        total_count = data.get('total_count')
        photos = data.get('photos')

        return UserProfilePhotos(data, total_count, photos)
