from . import base
from . import fields
from .location import Location
from .user import User


class InlineQuery(base.TelegramObject):
    """
    This object represents an incoming inline query.

    When the user sends an empty query, your bot could return some default or trending results.

    https://core.telegram.org/bots/api#inlinequery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    location: Location = fields.Field(base=Location)
    query: base.String = fields.Field()
    offset: base.String = fields.Field()
