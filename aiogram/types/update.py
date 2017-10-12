from . import base
from . import fields
import typing
from .message import Message
from .inline_query import InlineQuery
from .chosen_inline_result import ChosenInlineResult
from .callback_query import CallbackQuery
from .shipping_query import ShippingQuery
from .pre_checkout_query import PreCheckoutQuery


class Update(base.TelegramObject):
    """
    This object represents an incoming update.
    At most one of the optional parameters can be present in any given update.

    https://core.telegram.org/bots/api#update
    """
    update_id: base.Integer = fields.Field()
    message: Message = fields.Field(base=Message)
    edited_message: Message = fields.Field(base=Message)
    channel_post: Message = fields.Field(base=Message)
    edited_channel_post: Message = fields.Field(base=Message)
    inline_query: InlineQuery = fields.Field(base=InlineQuery)
    chosen_inline_result: ChosenInlineResult = fields.Field(base=ChosenInlineResult)
    callback_query: CallbackQuery = fields.Field(base=CallbackQuery)
    shipping_query: ShippingQuery = fields.Field(base=ShippingQuery)
    pre_checkout_query: PreCheckoutQuery = fields.Field(base=PreCheckoutQuery)

