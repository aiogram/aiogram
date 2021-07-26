from . import base
from . import fields


class MessageAutoDeleteTimerChanged(base.TelegramObject):
    """
    This object represents a service message about a change in auto-delete timer settings.

    https://core.telegram.org/bots/api#messageautodeletetimerchanged
    """
    message_auto_delete_time: base.Integer = fields.Field()
