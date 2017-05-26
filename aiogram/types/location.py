from . import Deserializable


class Location(Deserializable):
    __slots__ = ('data', 'longitude', 'latitude')

    def __init__(self, data, longitude, latitude):
        self.data = data
        self.longitude = longitude
        self.latitude = latitude

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        longitude = data.get('longitude')
        latitude = data.get('latitude')

        return Location(data, longitude, latitude)
