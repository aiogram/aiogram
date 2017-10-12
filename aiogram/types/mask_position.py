from . import base
from . import fields


class MaskPosition(base.TelegramObject):
    """
    This object describes the position on faces where a mask should be placed by default.

    https://core.telegram.org/bots/api#maskposition
    """
    point: base.String = fields.Field()
    x_shift: base.Float = fields.Field()
    y_shift: base.Float = fields.Field()
    scale: base.Float = fields.Field()
