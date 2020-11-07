from . import base, fields


class MessageId(base.TelegramObject):
    """
    This object represents a unique message identifier.

    https://core.telegram.org/bots/api#messageid
    """
    message_id: base.String = fields.Field()
