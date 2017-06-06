from .base import Deserializable
from .order_info import OrderInfo


class SuccessfulPayment(Deserializable):
    """
    This object contains basic information about a successful payment.
    
    https://core.telegram.org/bots/api#successfulpayment
    """
    def __init__(self, currency, total_amount, invoice_payload, shipping_option_id, order_info,
                 telegram_payment_charge_id, provider_payment_charge_id):
        self.currency: str = currency
        self.total_amount: int = total_amount
        self.invoice_payload: str = invoice_payload
        self.shipping_option_id: str = shipping_option_id
        self.order_info: OrderInfo = order_info
        self.telegram_payment_charge_id: str = telegram_payment_charge_id
        self.provider_payment_charge_id: str = provider_payment_charge_id

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        currency = raw_data.get('currency')
        total_amount = raw_data.get('total_amount')
        invoice_payload = raw_data.get('invoice_payload')
        shipping_option_id = raw_data.get('shipping_option_id')
        order_info = OrderInfo.deserialize(raw_data.get('order_info'))
        telegram_payment_charge_id = raw_data.get('telegram_payment_charge_id')
        provider_payment_charge_id = raw_data.get('provider_payment_charge_id')

        return SuccessfulPayment(currency, total_amount, invoice_payload, shipping_option_id, order_info,
                                 telegram_payment_charge_id, provider_payment_charge_id)
