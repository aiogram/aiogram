import typing

from . import base
from . import fields
from .photo_size import PhotoSize
from .sticker import Sticker
from ..utils.deprecated import warn_deprecated


class StickerSet(base.TelegramObject):
    """
    This object represents a sticker set.

    https://core.telegram.org/bots/api#stickerset
    """
    name: base.String = fields.Field()
    title: base.String = fields.Field()
    sticker_type: base.String = fields.Field()
    is_animated: base.Boolean = fields.Field()
    is_video: base.Boolean = fields.Field()
    contains_masks: base.Boolean = fields.Field()  # Deprecated
    stickers: typing.List[Sticker] = fields.ListField(base=Sticker)
    thumb: PhotoSize = fields.Field(base=PhotoSize)  # Deprecated
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)

    def __init__(
            self,
            name: base.String,
            title: base.String,
            sticker_type: base.String,
            is_animated: base.Boolean,
            is_video: base.Boolean,
            contains_masks: typing.Optional[base.Boolean] = None,
            stickers: typing.List[Sticker] = None,
            thumb: typing.Optional[PhotoSize] = None,
            thumbnail: typing.Optional[PhotoSize] = None,
    ):
        if not thumbnail and thumb:
            thumbnail = thumb
            warn_deprecated(
                "thumb is deprecated. Use thumbnail instead",
            )

        super().__init__(
            name=name,
            title=title,
            sticker_type=sticker_type,
            is_animated=is_animated,
            is_video=is_video,
            contains_masks=contains_masks,
            stickers=stickers,
            thumbnail=thumbnail,
        )
