from . import base
from . import fields


class LabeledPrice(base.TelegramObject):
    """
    This object represents a portion of the price for goods or services.

    https://core.telegram.org/bots/api#labeledprice
    """
    label: base.String = fields.Field()
    amount: base.Integer = fields.Field()
