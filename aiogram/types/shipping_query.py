from . import base
from . import fields
import typing
from .user import User
from .shipping_address import ShippingAddress


class ShippingQuery(base.TelegramObject):
    """
    This object contains information about an incoming shipping query.

    https://core.telegram.org/bots/api#shippingquery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    invoice_payload: base.String = fields.Field()
    shipping_address: ShippingAddress = fields.Field(base=ShippingAddress)

