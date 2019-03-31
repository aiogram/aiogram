from . import base
from . import fields
from .location import Location


class Venue(base.TelegramObject):
    """
    This object represents a venue.

    https://core.telegram.org/bots/api#venue
    """
    location: Location = fields.Field(base=Location)
    title: base.String = fields.Field()
    address: base.String = fields.Field()
    foursquare_id: base.String = fields.Field()
    foursquare_type: base.String = fields.Field()
