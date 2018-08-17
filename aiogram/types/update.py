from __future__ import annotations

from . import base
from . import fields
from .callback_query import CallbackQuery
from .chosen_inline_result import ChosenInlineResult
from .inline_query import InlineQuery
from .message import Message
from .pre_checkout_query import PreCheckoutQuery
from .shipping_query import ShippingQuery
from ..utils import helper


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

    def __hash__(self):
        return self.update_id

    def __int__(self):
        return self.update_id


class AllowedUpdates(helper.Helper):
    """
    Helper for allowed_updates parameter in getUpdates and setWebhook methods.

    You can use &, + or | operators for make combination of allowed updates.

    Example:
        >>> bot.get_updates(allowed_updates=AllowedUpdates.MESSAGE + AllowedUpdates.EDITED_MESSAGE)
    """
    mode = helper.HelperMode.snake_case

    MESSAGE = helper.ListItem()  # message
    EDITED_MESSAGE = helper.ListItem()  # edited_message
    CHANNEL_POST = helper.ListItem()  # channel_post
    EDITED_CHANNEL_POST = helper.ListItem()  # edited_channel_post
    INLINE_QUERY = helper.ListItem()  # inline_query
    CHOSEN_INLINE_QUERY = helper.ListItem()  # chosen_inline_result
    CALLBACK_QUERY = helper.ListItem()  # callback_query
    SHIPPING_QUERY = helper.ListItem()  # shipping_query
    PRE_CHECKOUT_QUERY = helper.ListItem()  # pre_checkout_query
