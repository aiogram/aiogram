from . import base
from . import fields


class PhotoSize(base.TelegramObject):
    """
    This object represents one size of a photo or a file / sticker thumbnail.

    https://core.telegram.org/bots/api#photosize
    """
    file_id: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    file_size: base.Integer = fields.Field()
