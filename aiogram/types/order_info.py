from .base import Deserializable
from .shipping_address import ShippingAddress


class OrderInfo(Deserializable):
    """
    his object represents information about an order.
    
    https://core.telegram.org/bots/api#orderinfo
    """
    def __init__(self, name, phone_number, email, shipping_address):
        self.name: str = name
        self.phone_number: str = phone_number
        self.email: str = email
        self.shipping_address: ShippingAddress = shipping_address

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        name = raw_data.get('name')
        phone_number = raw_data.get('phone_number')
        email = raw_data.get('email')
        shipping_address = ShippingAddress.deserialize(raw_data.get('shipping_address'))

        return OrderInfo(name, phone_number, email, shipping_address)
