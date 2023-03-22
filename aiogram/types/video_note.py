import typing

from . import base
from . import fields
from . import mixins
from .photo_size import PhotoSize
from ..utils.deprecated import warn_deprecated


class VideoNote(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a video message (available in Telegram apps as of v.4.0).

    https://core.telegram.org/bots/api#videonote
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    length: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)  # Deprecated
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)
    file_size: base.Integer = fields.Field()

    def __init__(
            self,
            file_id: base.String,
            file_unique_id: base.String,
            length: base.Integer,
            duration: base.Integer,
            thumb: typing.Optional[PhotoSize] = None,
            thumbnail: typing.Optional[PhotoSize] = None,
            file_size: typing.Optional[base.Integer] = None,
    ):
        if not thumbnail and thumb:
            thumbnail = thumb
            warn_deprecated(
                "thumb is deprecated. Use thumbnail instead",
            )

        super().__init__(
            file_id=file_id,
            file_unique_id=file_unique_id,
            length=length,
            duration=duration,
            thumbnail=thumbnail,
            file_size=file_size,
        )
