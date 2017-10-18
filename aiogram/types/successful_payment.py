from . import base
from . import fields
from .order_info import OrderInfo


class SuccessfulPayment(base.TelegramObject):
    """
    This object contains basic information about a successful payment.

    https://core.telegram.org/bots/api#successfulpayment
    """
    currency: base.String = fields.Field()
    total_amount: base.Integer = fields.Field()
    invoice_payload: base.String = fields.Field()
    shipping_option_id: base.String = fields.Field()
    order_info: OrderInfo = fields.Field(base=OrderInfo)
    telegram_payment_charge_id: base.String = fields.Field()
    provider_payment_charge_id: base.String = fields.Field()
