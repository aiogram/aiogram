from . import base
from . import fields


class SentWebAppMessage(base.TelegramObject):
    """
    Contains information about an inline message sent by a Web App on behalf of a user.

    Source: https://core.telegram.org/bots/api#sentwebappmessage
    """
    inline_message_id: base.String = fields.Field()
