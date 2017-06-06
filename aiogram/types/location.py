from .base import Deserializable


class Location(Deserializable):
    """
    This object represents a point on the map.
    
    https://core.telegram.org/bots/api#location
    """
    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        longitude = raw_data.get('longitude')
        latitude = raw_data.get('latitude')

        return Location(longitude, latitude)
