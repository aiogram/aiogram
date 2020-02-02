from . import base
from . import fields
from . import mixins
from .photo_size import PhotoSize


class Document(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a general file (as opposed to photos, voice messages and audio files).

    https://core.telegram.org/bots/api#document
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    file_name: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()
