from . import base
from . import fields
from .user import User


class ProximityAlertTriggered(base.TelegramObject):
    """
    This object represents the content of a service message, sent whenever a user in
    the chat triggers a proximity alert set by another user.

    https://core.telegram.org/bots/api#proximityalerttriggered
    """
    traveler: User = fields.Field()
    watcher: User = fields.Field()
    distance: base.Integer = fields.Field()
