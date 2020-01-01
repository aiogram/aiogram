from . import base
from . import fields
from . import mixins
from .photo_size import PhotoSize


class VideoNote(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a video message (available in Telegram apps as of v.4.0).

    https://core.telegram.org/bots/api#videonote
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    length: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    file_size: base.Integer = fields.Field()
