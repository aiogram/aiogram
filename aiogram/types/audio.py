from . import base
from . import fields
from . import mixins
from .photo_size import PhotoSize
from ..utils.deprecated import warn_deprecated


class Audio(base.TelegramObject, mixins.Downloadable):
    """
    This object represents an audio file to be treated as music by the Telegram clients.

    https://core.telegram.org/bots/api#audio
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    duration: base.Integer = fields.Field()
    performer: base.String = fields.Field()
    title: base.String = fields.Field()
    file_name: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)

    @property
    def thumb(self):
        warn_deprecated(
            "thumb is deprecated. Use thumbnail instead",
        )
        return self.thumbnail
