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
    thumbnail: PhotoSize = fields.Field(base=PhotoSize)

    @property
    def thumb(self):
        warn_deprecated('thumb is deprecated, use thumbnail instead')
        return self.thumbnail
