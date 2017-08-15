from .base import Deserializable
from .callback_query import CallbackQuery
from .chosen_inline_result import ChosenInlineResult
from .inline_query import InlineQuery
from .message import Message
from .pre_checkout_query import PreCheckoutQuery
from .shipping_query import ShippingQuery
from ..utils.helper import Helper, ListItem, HelperMode


class Update(Deserializable):
    """
    This object represents an incoming update.
    
    At most one of the optional parameters can be present in any given update.
    
    https://core.telegram.org/bots/api#update
    """

    def __init__(self, update_id, message, edited_message, channel_post, edited_channel_post, inline_query,
                 chosen_inline_result, callback_query, shipping_query, pre_checkout_query):
        self.update_id: int = update_id
        self.message: Message = message
        self.edited_message: Message = edited_message
        self.channel_post: Message = channel_post
        self.edited_channel_post: Message = edited_channel_post
        self.inline_query: InlineQuery = inline_query
        self.chosen_inline_result: ChosenInlineResult = chosen_inline_result
        self.callback_query: CallbackQuery = callback_query
        self.shipping_query: ShippingQuery = shipping_query
        self.pre_checkout_query: PreCheckoutQuery = pre_checkout_query

    @classmethod
    def de_json(cls, raw_data):
        update_id = raw_data.get('update_id')
        message = Message.deserialize(raw_data.get('message'))
        edited_message = Message.deserialize(raw_data.get('edited_message'))
        channel_post = Message.deserialize(raw_data.get('channel_post'))
        edited_channel_post = Message.deserialize(raw_data.get('edited_channel_post'))

        inline_query = InlineQuery.deserialize(raw_data.get('inline_query'))
        chosen_inline_result = ChosenInlineResult.deserialize(raw_data.get('chosen_inline_result'))
        callback_query = CallbackQuery.deserialize(raw_data.get('callback_query'))
        shipping_query = ShippingQuery.deserialize(raw_data.get('shipping_query'))
        pre_checkout_query = PreCheckoutQuery.deserialize(raw_data.get('pre_checkout_query'))

        return Update(update_id, message, edited_message, channel_post, edited_channel_post, inline_query,
                      chosen_inline_result, callback_query, shipping_query, pre_checkout_query)


class AllowedUpdates(Helper):
    """
    Helper for allowed_updates parameter in getUpdates and setWebhook methods.

    You can use &, + or | operators for make combination of allowed updates.

    Example:
        >>> bot.get_updates(allowed_updates=AllowedUpdates.MESSAGE + AllowedUpdates.EDITED_MESSAGE)
    """
    mode = HelperMode.snake_case

    MESSAGE = ListItem()  # message
    EDITED_MESSAGE = ListItem()  # edited_message
    CHANNEL_POST = ListItem()  # channel_post
    EDITED_CHANNEL_POST = ListItem()  # edited_channel_post
    INLINE_QUERY = ListItem()  # inline_query
    CHOSEN_INLINE_QUERY = ListItem()  # chosen_inline_result
    CALLBACK_QUERY = ListItem()  # callback_query
    SHIPPING_QUERY = ListItem()  # shipping_query
    PRE_CHECKOUT_QUERY = ListItem()  # pre_checkout_query
