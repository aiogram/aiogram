from . import base
from . import fields


class ResponseParameters(base.TelegramObject):
    """
    Contains information about why a request was unsuccessful.

    https://core.telegram.org/bots/api#responseparameters
    """
    migrate_to_chat_id: base.Integer = fields.Field()
    retry_after: base.Integer = fields.Field()
