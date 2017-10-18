from . import base
from . import fields


class ShippingAddress(base.TelegramObject):
    """
    This object represents a shipping address.

    https://core.telegram.org/bots/api#shippingaddress
    """
    country_code: base.String = fields.Field()
    state: base.String = fields.Field()
    city: base.String = fields.Field()
    street_line1: base.String = fields.Field()
    street_line2: base.String = fields.Field()
    post_code: base.String = fields.Field()
