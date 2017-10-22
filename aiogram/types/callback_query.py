from . import base
from . import fields
from .message import Message
from .user import User


class CallbackQuery(base.TelegramObject):
    """
    This object represents an incoming callback query from a callback button in an inline keyboard.

    If the button that originated the query was attached to a message sent by the bot,
    the field message will be present.

    If the button was attached to a message sent via the bot (in inline mode),
    the field inline_message_id will be present.

    Exactly one of the fields data or game_short_name will be present.

    https://core.telegram.org/bots/api#callbackquery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    message: Message = fields.Field(base=Message)
    inline_message_id: base.String = fields.Field()
    chat_instance: base.String = fields.Field()
    data: base.String = fields.Field()
    game_short_name: base.String = fields.Field()

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.id == self.id
        return self.id == other
