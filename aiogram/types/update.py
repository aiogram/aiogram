from aiogram.types import Deserializable
from aiogram.types.message import Message


class Update(Deserializable):
    __slots__ = ('update_id', 'message', 'edited_message', 'channel_post', 'edited_channel_post', 'inline_query',
                 'chosen_inline_result', 'callback_query', 'shipping_query', 'pre_checkout_query')

    def __init__(self, data, update_id, message, edited_message, channel_post, edited_channel_post, inline_query,
                 chosen_inline_result, callback_query, shipping_query, pre_checkout_query):
        self.data = data

        self.update_id = update_id
        self.message: Message = message
        self.edited_message: Message = edited_message
        self.channel_post: Message = channel_post
        self.edited_channel_post: Message = edited_channel_post
        self.inline_query = inline_query
        self.chosen_inline_result = chosen_inline_result
        self.callback_query = callback_query
        self.shipping_query = shipping_query
        self.pre_checkout_query = pre_checkout_query

    @classmethod
    def _parse_message(cls, message):
        return Message.de_json(message) if message else None

    @classmethod
    def de_json(cls, data):
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
        :param data: 
        :return: 
        """
        data = cls.check_json(data)

        update_id = data.get('update_id')
        message = cls._parse_message(data.get('message'))
        edited_message = cls._parse_message(data.get('edited_message'))
        channel_post = cls._parse_message(data.get('channel_post'))
        edited_channel_post = cls._parse_message(data.get('edited_channel_post'))

        inline_query = data.get('inline_query')
        chosen_inline_result = data.get('chosen_inline_result')
        callback_query = data.get('callback_query')
        shipping_query = data.get('shipping_query')
        pre_checkout_query = data.get('pre_checkout_query')

        return Update(data, update_id, message, edited_message, channel_post, edited_channel_post, inline_query,
                      chosen_inline_result, callback_query, shipping_query, pre_checkout_query)
