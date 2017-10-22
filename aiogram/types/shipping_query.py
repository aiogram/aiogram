from . import base
from . import fields
from .shipping_address import ShippingAddress
from .user import User


class ShippingQuery(base.TelegramObject):
    """
    This object contains information about an incoming shipping query.

    https://core.telegram.org/bots/api#shippingquery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    invoice_payload: base.String = fields.Field()
    shipping_address: ShippingAddress = fields.Field(base=ShippingAddress)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.id == self.id
        return self.id == other
