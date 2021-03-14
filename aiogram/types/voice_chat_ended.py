from . import base
from . import fields
from . import mixins


class VoiceChatEnded(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a service message about a voice chat ended in the chat.

    https://core.telegram.org/bots/api#voicechatended
    """

    duration: base.Integer = fields.Field()
