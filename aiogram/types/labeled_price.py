from . import base
from . import fields


class LabeledPrice(base.TelegramObject):
    """
    This object represents a portion of the price for goods or services.

    https://core.telegram.org/bots/api#labeledprice
    """
    label: base.String = fields.Field()
    amount: base.Integer = fields.Field()

    def __init__(self, label: base.String, amount: base.Integer):
        super(LabeledPrice, self).__init__(label=label, amount=amount)
