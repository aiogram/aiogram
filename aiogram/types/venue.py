from . import Deserializable


class Venue(Deserializable):
    __slots__ = ('data', 'location', 'title', 'address', 'foursquare_id')

    def __init__(self, data, location, title, address, foursquare_id):
        self.data = data
        self.location = location
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        location = data.get('location')
        title = data.get('title')
        address = data.get('address')
        foursquare_id = data.get('foursquare_id')

        return Venue(data, location, title, address, foursquare_id)
