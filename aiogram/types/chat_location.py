from . import base
from . import fields
from .location import Location


class ChatLocation(base.TelegramObject):
    """
    Represents a location to which a chat is connected.

    https://core.telegram.org/bots/api#chatlocation
    """
    location: Location = fields.Field()
    address: base.String = fields.Field()

    def __init__(self, location: Location, address: base.String):
        super().__init__(location=location, address=address)
