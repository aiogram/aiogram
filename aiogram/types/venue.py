from .base import Deserializable
from .location import Location


class Venue(Deserializable):
    """
    This object represents a venue.
    
    https://core.telegram.org/bots/api#venue
    """
    def __init__(self, location, title, address, foursquare_id):
        self.location: Location = location
        self.title: str = title
        self.address: str = address
        self.foursquare_id: str = foursquare_id

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        location = Location.deserialize(raw_data.get('location'))
        title = raw_data.get('title')
        address = raw_data.get('address')
        foursquare_id = raw_data.get('foursquare_id')

        return Venue(location, title, address, foursquare_id)
