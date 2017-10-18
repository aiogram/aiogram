import typing

from . import base
from . import fields
from .labeled_price import LabeledPrice


class ShippingOption(base.TelegramObject):
    """
    This object represents one shipping option.

    https://core.telegram.org/bots/api#shippingoption
    """
    id: base.String = fields.Field()
    title: base.String = fields.Field()
    prices: typing.List[LabeledPrice] = fields.ListField(base=LabeledPrice)

    def __init__(self, id: base.String, title: base.String, prices: typing.List[LabeledPrice] = None):
        if prices is None:
            prices = []

        super(ShippingOption, self).__init__(id=id, title=title, prices=prices)

    def add(self, price: LabeledPrice):
        """
        Add price

        :param price:
        :return:
        """
        self.prices.append(price)
        return self
