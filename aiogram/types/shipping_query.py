from .base import Deserializable
from .shipping_address import ShippingAddress
from .user import User


class ShippingQuery(Deserializable):
    """
    This object contains information about an incoming shipping query.
    
    https://core.telegram.org/bots/api#shippingquery
    """
    def __init__(self, id, from_user, invoice_payload, shipping_address):
        self.id: str = id
        self.from_user: User = from_user
        self.invoice_payload: str = invoice_payload
        self.shipping_address: ShippingAddress = shipping_address

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        id = raw_data.get('id')
        from_user = User.deserialize(raw_data.get('from'))
        invoice_payload = raw_data.get('invoice_payload')
        shipping_address = ShippingAddress.deserialize(raw_data.get('shipping_address'))

        return ShippingQuery(id, from_user, invoice_payload, shipping_address)
