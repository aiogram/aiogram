import logging
import time

from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

HANDLED_STR = ['Unhandled', 'Handled']


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, logger=__name__):
        if not isinstance(logger, logging.Logger):
            logger = logging.getLogger(logger)

        self.logger = logger

        super(LoggingMiddleware, self).__init__()

    def check_timeout(self, obj):
        start = obj.conf.get('_start', None)
        if start:
            del obj.conf['_start']
            return round((time.time() - start) * 1000)
        return -1

    async def on_pre_process_update(self, update: types.Update):
        update.conf['_start'] = time.time()
        self.logger.debug(f"Received update [ID:{update.update_id}]")

    async def on_post_process_update(self, update: types.Update, result):
        timeout = self.check_timeout(update)
        if timeout > 0:
            self.logger.info(f"Process update [ID:{update.update_id}]: [success] (in {timeout} ms)")

    async def on_pre_process_message(self, message: types.Message):
        self.logger.info(f"Received message [ID:{message.message_id}] in chat [{message.chat.type}:{message.chat.id}]")

    async def on_post_process_message(self, message: types.Message, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"message [ID:{message.message_id}] in chat [{message.chat.type}:{message.chat.id}]")

    async def on_pre_process_edited_message(self, edited_message):
        self.logger.info(f"Received edited message [ID:{edited_message.message_id}] "
                         f"in chat [{edited_message.chat.type}:{edited_message.chat.id}]")

    async def on_post_process_edited_message(self, edited_message, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"edited message [ID:{edited_message.message_id}] "
                          f"in chat [{edited_message.chat.type}:{edited_message.chat.id}]")

    async def on_pre_process_channel_post(self, channel_post: types.Message):
        self.logger.info(f"Received channel post [ID:{channel_post.message_id}] "
                         f"in channel [ID:{channel_post.chat.id}]")

    async def on_post_process_channel_post(self, channel_post: types.Message, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"channel post [ID:{channel_post.message_id}] "
                          f"in chat [{channel_post.chat.type}:{channel_post.chat.id}]")

    async def on_pre_process_edited_channel_post(self, edited_channel_post: types.Message):
        self.logger.info(f"Received edited channel post [ID:{edited_channel_post.message_id}] "
                         f"in channel [ID:{edited_channel_post.chat.id}]")

    async def on_post_process_edited_channel_post(self, edited_channel_post: types.Message, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"edited channel post [ID:{edited_channel_post.message_id}] "
                          f"in channel [ID:{edited_channel_post.chat.id}]")

    async def on_pre_process_inline_query(self, inline_query: types.InlineQuery):
        self.logger.info(f"Received inline query [ID:{inline_query.id}] "
                         f"from user [ID:{inline_query.from_user.id}]")

    async def on_post_process_inline_query(self, inline_query: types.InlineQuery, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"inline query [ID:{inline_query.id}] "
                          f"from user [ID:{inline_query.from_user.id}]")

    async def on_pre_process_chosen_inline_result(self, chosen_inline_result: types.ChosenInlineResult):
        self.logger.info(f"Received chosen inline result [Inline msg ID:{chosen_inline_result.inline_message_id}] "
                         f"from user [ID:{chosen_inline_result.from_user.id}] "
                         f"result [ID:{chosen_inline_result.result_id}]")

    async def on_post_process_chosen_inline_result(self, chosen_inline_result, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"chosen inline result [Inline msg ID:{chosen_inline_result.inline_message_id}] "
                          f"from user [ID:{chosen_inline_result.from_user.id}] "
                          f"result [ID:{chosen_inline_result.result_id}]")

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery):
        if callback_query.message:
            self.logger.info(f"Received callback query [ID:{callback_query.id}] "
                             f"in chat [{callback_query.message.chat.type}:{callback_query.message.chat.id}] "
                             f"from user [ID:{callback_query.message.from_user.id}]")
        else:
            self.logger.info(f"Received callback query [ID:{callback_query.id}] "
                             f"from inline message [ID:{callback_query.inline_message_id}] "
                             f"from user [ID:{callback_query.from_user.id}]")

    async def on_post_process_callback_query(self, callback_query, results):
        if callback_query.message:
            self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                              f"callback query [ID:{callback_query.id}] "
                              f"in chat [{callback_query.message.chat.type}:{callback_query.message.chat.id}] "
                              f"from user [ID:{callback_query.message.from_user.id}]")
        else:
            self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                              f"callback query [ID:{callback_query.id}] "
                              f"from inline message [ID:{callback_query.inline_message_id}] "
                              f"from user [ID:{callback_query.from_user.id}]")

    async def on_pre_process_shipping_query(self, shipping_query: types.ShippingQuery):
        self.logger.info(f"Received shipping query [ID:{shipping_query.id}] "
                         f"from user [ID:{shipping_query.from_user.id}]")

    async def on_post_process_shipping_query(self, shipping_query, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"shipping query [ID:{shipping_query.id}] "
                          f"from user [ID:{shipping_query.from_user.id}]")

    async def on_pre_process_pre_checkout_query(self, pre_checkout_query: types.PreCheckoutQuery):
        self.logger.info(f"Received pre-checkout query [ID:{pre_checkout_query.id}] "
                         f"from user [ID:{pre_checkout_query.from_user.id}]")

    async def on_post_process_pre_checkout_query(self, pre_checkout_query, results):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"pre-checkout query [ID:{pre_checkout_query.id}] "
                          f"from user [ID:{pre_checkout_query.from_user.id}]")

    async def on_pre_process_error(self, dispatcher, update, error):
        timeout = self.check_timeout(update)
        if timeout > 0:
            self.logger.info(f"Process update [ID:{update.update_id}]: [failed] (in {timeout} ms)")
