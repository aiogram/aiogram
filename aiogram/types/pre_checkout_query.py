from .base import Deserializable
from .order_info import OrderInfo
from .user import User


class PreCheckoutQuery(Deserializable):
    """
    This object contains information about an incoming pre-checkout query.
    
    https://core.telegram.org/bots/api#precheckoutquery
    """
    def __init__(self, id, from_user, currency, total_amount, invoice_payload, shipping_option_id, order_info):
        self.id: str = id
        self.from_user: User = from_user
        self.currency: str = currency
        self.total_amount: int = total_amount
        self.invoice_payload: str = invoice_payload
        self.shipping_option_id: str = shipping_option_id
        self.order_info: OrderInfo = order_info

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        id = raw_data.get('id')
        from_user = User.deserialize(raw_data.get('from'))
        currency = raw_data.get('currency')
        total_amount = raw_data.get('total_amount')
        invoice_payload = raw_data.get('invoice_payload')
        shipping_option_id = raw_data.get('shipping_option_id')
        order_info = OrderInfo.deserialize(raw_data.get('order_info'))

        return PreCheckoutQuery(id, from_user, currency, total_amount, invoice_payload, shipping_option_id, order_info)
