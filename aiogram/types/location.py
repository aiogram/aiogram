from . import Deserializable


class Location(Deserializable):
    __slots__ = ('longitude', 'latitude')

    def __init__(self, data, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        longitude = raw_data.get('longitude')
        latitude = raw_data.get('latitude')

        return Location(longitude, latitude)
