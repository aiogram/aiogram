from . import base
from . import fields
from . import mixins
from .mask_position import MaskPosition
from .photo_size import PhotoSize


class Sticker(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a sticker.

    https://core.telegram.org/bots/api#sticker
    """
    file_id: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    thumb: PhotoSize = fields.Field(base=PhotoSize)
    emoji: base.String = fields.Field()
    set_name: base.String = fields.Field()
    mask_position: MaskPosition = fields.Field(base=MaskPosition)
    file_size: base.Integer = fields.Field()
