from . import base
from . import fields


class Location(base.TelegramObject):
    """
    This object represents a point on the map.

    https://core.telegram.org/bots/api#location
    """
    longitude: base.Float = fields.Field()
    latitude: base.Float = fields.Field()
