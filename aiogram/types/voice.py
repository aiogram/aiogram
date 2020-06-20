from . import base
from . import fields
from . import mixins


class Voice(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a voice note.

    https://core.telegram.org/bots/api#voice
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    duration: base.Integer = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()
