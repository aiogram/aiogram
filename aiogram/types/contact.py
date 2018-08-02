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
    vcard: base.String = fields.Field()

    @property
    def full_name(self):
        name = self.first_name
        if self.last_name is not None:
            name += ' ' + self.last_name
        return name

    def __hash__(self):
        return hash(self.phone_number)
