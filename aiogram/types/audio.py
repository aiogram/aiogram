import typing

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
    thumb: PhotoSize = fields.Field(base=PhotoSize)  # Deprecated
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)

    def __init__(
            self,
            file_id: base.String,
            file_unique_id: base.String,
            duration: base.Integer,
            performer: typing.Optional[base.String] = None,
            title: typing.Optional[base.String] = None,
            file_name: typing.Optional[base.String] = None,
            mime_type: typing.Optional[base.String] = None,
            file_size: typing.Optional[base.Integer] = None,
            thumb: typing.Optional[PhotoSize] = None,
            thumbnail: typing.Optional[PhotoSize] = None,
    ):
        if not thumbnail and thumb:
            thumbnail = thumb
            warn_deprecated(
                "thumb is deprecated. Use thumbnail instead",
            )

        super().__init__(
            file_id=file_id,
            file_unique_id=file_unique_id,
            duration=duration,
            performer=performer,
            title=title,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
            thumbnail=thumbnail,
        )
