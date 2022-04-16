from . import base
from . import fields
from . import mixins


class VideoChatEnded(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a service message about a video chat scheduled in the chat.

    https://core.telegram.org/bots/api#videochatended
    """

    duration: base.Integer = fields.Field()
