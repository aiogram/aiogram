from . import base
from . import fields
from .location import Location
from .user import User


class ChosenInlineResult(base.TelegramObject):
    """
    Represents a result of an inline query that was chosen by the user and sent to their chat partner.

    Note: It is necessary to enable inline feedback via @Botfather in order to receive these objects in updates.
    Your bot can accept payments from Telegram users.
    Please see the introduction to payments for more details on the process and how to set up payments for your bot.
    Please note that users will need Telegram v.4.0 or higher to use payments (released on May 18, 2017).

    https://core.telegram.org/bots/api#choseninlineresult
    """
    result_id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    location: Location = fields.Field(base=Location)
    inline_message_id: base.String = fields.Field()
    query: base.String = fields.Field()
