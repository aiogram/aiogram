from . import base
from . import fields
from . import mixins


class PhotoSize(base.TelegramObject, mixins.Downloadable):
    """
    This object represents one size of a photo or a file / sticker thumbnail.

    https://core.telegram.org/bots/api#photosize
    """
    file_id: base.String = fields.Field()
    file_unique_id: base.String = fields.Field()
    width: base.Integer = fields.Field()
    height: base.Integer = fields.Field()
    file_size: base.Integer = fields.Field()
