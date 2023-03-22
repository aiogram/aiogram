import typing

from . import base
from . import fields
from . import mixins
from .photo_size import PhotoSize
from ..utils.deprecated import warn_deprecated


class Animation(base.TelegramObject, mixins.Downloadable):
    """
    You can provide an animation for your game so that it looks stylish in chats
    (check out Lumberjack for an example).
    This object represents an animation file to be displayed in the message containing a game.

    https://core.telegram.org/bots/api#animation
    """

    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    duration: base.Integer = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)  # Deprecated
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)
    file_name: base.String = fields.Field()
    mime_type: base.String = fields.Field()
    file_size: base.Integer = fields.Field()

    def __init__(
            self,
            file_id: base.String,
            file_unique_id: base.String,
            width: base.Integer,
            height: base.Integer,
            duration: base.Integer,
            thumb: typing.Optional[PhotoSize] = None,
            thumbnail: typing.Optional[PhotoSize] = None,
            file_name: typing.Optional[base.String] = None,
            mime_type: typing.Optional[base.String] = None,
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
            width=width,
            height=height,
            duration=duration,
            thumbnail=thumbnail,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
        )
