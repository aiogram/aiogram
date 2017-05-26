from . import Deserializable


class Venue(Deserializable):
    __slots__ = ('location', 'title', 'address', 'foursquare_id')

    def __init__(self, location, title, address, foursquare_id):
        self.location = location
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        location = raw_data.get('location')
        title = raw_data.get('title')
        address = raw_data.get('address')
        foursquare_id = raw_data.get('foursquare_id')

        return Venue(location, title, address, foursquare_id)
