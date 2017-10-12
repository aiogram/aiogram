from . import base
from . import fields


class Contact(base.TelegramObject):
    """
    This object represents a phone contact.

    https://core.telegram.org/bots/api#contact
    """
    phone_number: base.String = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    user_id: base.Integer = fields.Field()
