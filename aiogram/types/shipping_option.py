from . import base
from . import fields
import typing
from .labeled_price import LabeledPrice


class ShippingOption(base.TelegramObject):
    """
    This object represents one shipping option.

    https://core.telegram.org/bots/api#shippingoption
    """
    id: base.String = fields.Field()
    title: base.String = fields.Field()
    prices: typing.List[LabeledPrice] = fields.ListField(base=LabeledPrice)

