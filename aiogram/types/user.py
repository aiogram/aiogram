from . import base
from . import fields
import typing


class User(base.TelegramObject):
    """
    This object represents a Telegram user or bot.

    https://core.telegram.org/bots/api#user
    """
    id: base.Integer = fields.Field()
    is_bot: base.Boolean = fields.Field()
    first_name: base.String = fields.Field()
    last_name: base.String = fields.Field()
    username: base.String = fields.Field()
    language_code: base.String = fields.Field()

