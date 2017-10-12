from . import base
from . import fields


class Invoice(base.TelegramObject):
    """
    This object contains basic information about an invoice.

    https://core.telegram.org/bots/api#invoice
    """
    title: base.String = fields.Field()
    description: base.String = fields.Field()
    start_parameter: base.String = fields.Field()
    currency: base.String = fields.Field()
    total_amount: base.Integer = fields.Field()
