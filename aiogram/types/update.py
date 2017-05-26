from aiogram.types.callback_query import CallbackQuery
from aiogram.types.chosen_inline_result import ChosenInlineResult
from aiogram.types.inline_query import InlineQuery
from aiogram.types.pre_checkout_query import PreCheckoutQuery
from aiogram.types.shipping_query import ShippingQuery
from . import Deserializable
from .message import Message


class Update(Deserializable):
    def __init__(self, update_id, message, edited_maiogramessage, channel_post, edited_channel_post, inline_query,
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
        """
        update_id	Integer	The update‘s unique identifier. Update identifiers start from a certain positive number and increase sequentially. This ID becomes especially handy if you’re using Webhooks, since it allows you to ignore repeated updates or to restore the correct update sequence, should they get out of order.
        message	Message	Optional. New incoming message of any kind — text, photo, sticker, etc.
        edited_message	Message	Optional. New version of a message that is known to the bot and was edited
        channel_post	Message	Optional. New incoming channel post of any kind — text, photo, sticker, etc.
        edited_channel_post	Message	Optional. New version of a channel post that is known to the bot and was edited
        inline_query	InlineQuery	Optional. New incoming inline query
        chosen_inline_result	ChosenInlineResult	Optional. The result of an inline query that was chosen by a user and sent to their chat partner.
        callback_query	CallbackQuery	Optional. New incoming callback query
        shipping_query	ShippingQuery	Optional. New incoming shipping query. Only for invoices with flexible price
        pre_checkout_query	PreCheckoutQuery	Optional. New incoming pre-checkout query. Contains full information about checkout
        :param raw_data: 
        :return: 
        """
        raw_data = cls.check_json(raw_data)

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
