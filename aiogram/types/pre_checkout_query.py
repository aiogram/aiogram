from . import base
from . import fields
from .order_info import OrderInfo
from .user import User


class PreCheckoutQuery(base.TelegramObject):
    """
    This object contains information about an incoming pre-checkout query.
    Your bot can offer users HTML5 games to play solo or to compete against
    each other in groups and one-on-one chats.

    Create games via @BotFather using the /newgame command.

    Please note that this kind of power requires responsibility:
    you will need to accept the terms for each game that your bots will be offering.

    https://core.telegram.org/bots/api#precheckoutquery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    currency: base.String = fields.Field()
    total_amount: base.Integer = fields.Field()
    invoice_payload: base.String = fields.Field()
    shipping_option_id: base.String = fields.Field()
    order_info: OrderInfo = fields.Field(base=OrderInfo)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.id == self.id
        return self.id == other
