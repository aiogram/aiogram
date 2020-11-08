import typing

from . import base
from . import fields


class Location(base.TelegramObject):
    """
    This object represents a point on the map.

    https://core.telegram.org/bots/api#location
    """
    longitude: base.Float = fields.Field()
    latitude: base.Float = fields.Field()
    horizontal_accuracy: typing.Optional[base.Float] = fields.Field()
    live_period: typing.Optional[base.Integer] = fields.Field()
    heading: typing.Optional[base.Integer] = fields.Field()
    proximity_alert_radius: typing.Optional[base.Integer] = fields.Field()
