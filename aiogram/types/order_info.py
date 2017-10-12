from . import base
from . import fields
from .shipping_address import ShippingAddress


class OrderInfo(base.TelegramObject):
    """
    This object represents information about an order.

    https://core.telegram.org/bots/api#orderinfo
    """
    name: base.String = fields.Field()
    phone_number: base.String = fields.Field()
    email: base.String = fields.Field()
    shipping_address: ShippingAddress = fields.Field(base=ShippingAddress)
