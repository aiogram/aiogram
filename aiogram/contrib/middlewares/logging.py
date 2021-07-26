import time

import logging

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

    async def on_pre_process_update(self, update: types.Update, data: dict):
        update.conf['_start'] = time.time()
        self.logger.debug(f"Received update [ID:{update.update_id}]")

    async def on_post_process_update(self, update: types.Update, result, data: dict):
        timeout = self.check_timeout(update)
        if timeout > 0:
            self.logger.info(f"Process update [ID:{update.update_id}]: [success] (in {timeout} ms)")

    async def on_pre_process_message(self, message: types.Message, data: dict):
        self.logger.info(f"Received message [ID:{message.message_id}] in chat [{message.chat.type}:{message.chat.id}]")

    async def on_post_process_message(self, message: types.Message, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"message [ID:{message.message_id}] in chat [{message.chat.type}:{message.chat.id}]")

    async def on_pre_process_edited_message(self, edited_message, data: dict):
        self.logger.info(f"Received edited message [ID:{edited_message.message_id}] "
                         f"in chat [{edited_message.chat.type}:{edited_message.chat.id}]")

    async def on_post_process_edited_message(self, edited_message, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"edited message [ID:{edited_message.message_id}] "
                          f"in chat [{edited_message.chat.type}:{edited_message.chat.id}]")

    async def on_pre_process_channel_post(self, channel_post: types.Message, data: dict):
        self.logger.info(f"Received channel post [ID:{channel_post.message_id}] "
                         f"in channel [ID:{channel_post.chat.id}]")

    async def on_post_process_channel_post(self, channel_post: types.Message, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"channel post [ID:{channel_post.message_id}] "
                          f"in chat [{channel_post.chat.type}:{channel_post.chat.id}]")

    async def on_pre_process_edited_channel_post(self, edited_channel_post: types.Message, data: dict):
        self.logger.info(f"Received edited channel post [ID:{edited_channel_post.message_id}] "
                         f"in channel [ID:{edited_channel_post.chat.id}]")

    async def on_post_process_edited_channel_post(self, edited_channel_post: types.Message, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"edited channel post [ID:{edited_channel_post.message_id}] "
                          f"in channel [ID:{edited_channel_post.chat.id}]")

    async def on_pre_process_inline_query(self, inline_query: types.InlineQuery, data: dict):
        self.logger.info(f"Received inline query [ID:{inline_query.id}] "
                         f"from user [ID:{inline_query.from_user.id}]")

    async def on_post_process_inline_query(self, inline_query: types.InlineQuery, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"inline query [ID:{inline_query.id}] "
                          f"from user [ID:{inline_query.from_user.id}]")

    async def on_pre_process_chosen_inline_result(self, chosen_inline_result: types.ChosenInlineResult, data: dict):
        self.logger.info(f"Received chosen inline result [Inline msg ID:{chosen_inline_result.inline_message_id}] "
                         f"from user [ID:{chosen_inline_result.from_user.id}] "
                         f"result [ID:{chosen_inline_result.result_id}]")

    async def on_post_process_chosen_inline_result(self, chosen_inline_result, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"chosen inline result [Inline msg ID:{chosen_inline_result.inline_message_id}] "
                          f"from user [ID:{chosen_inline_result.from_user.id}] "
                          f"result [ID:{chosen_inline_result.result_id}]")

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        if callback_query.message:
            text = (f"Received callback query [ID:{callback_query.id}] "
                    f"from user [ID:{callback_query.from_user.id}] "
                    f"for message [ID:{callback_query.message.message_id}] "
                    f"in chat [{callback_query.message.chat.type}:{callback_query.message.chat.id}]")

            if callback_query.message.from_user:
                text += f" originally posted by user [ID:{callback_query.message.from_user.id}]"

            self.logger.info(text)

        else:
            self.logger.info(f"Received callback query [ID:{callback_query.id}] "
                             f"from user [ID:{callback_query.from_user.id}] "
                             f"for inline message [ID:{callback_query.inline_message_id}] ")

    async def on_post_process_callback_query(self, callback_query, results, data: dict):
        if callback_query.message:
            text = (f"{HANDLED_STR[bool(len(results))]} "
                    f"callback query [ID:{callback_query.id}] "
                    f"from user [ID:{callback_query.from_user.id}] "
                    f"for message [ID:{callback_query.message.message_id}] "
                    f"in chat [{callback_query.message.chat.type}:{callback_query.message.chat.id}]")

            if callback_query.message.from_user:
                text += f" originally posted by user [ID:{callback_query.message.from_user.id}]"

            self.logger.info(text)

        else:
            self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                              f"callback query [ID:{callback_query.id}] "
                              f"from user [ID:{callback_query.from_user.id}]"
                              f"from inline message [ID:{callback_query.inline_message_id}]")

    async def on_pre_process_shipping_query(self, shipping_query: types.ShippingQuery, data: dict):
        self.logger.info(f"Received shipping query [ID:{shipping_query.id}] "
                         f"from user [ID:{shipping_query.from_user.id}]")

    async def on_post_process_shipping_query(self, shipping_query, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"shipping query [ID:{shipping_query.id}] "
                          f"from user [ID:{shipping_query.from_user.id}]")

    async def on_pre_process_pre_checkout_query(self, pre_checkout_query: types.PreCheckoutQuery, data: dict):
        self.logger.info(f"Received pre-checkout query [ID:{pre_checkout_query.id}] "
                         f"from user [ID:{pre_checkout_query.from_user.id}]")

    async def on_post_process_pre_checkout_query(self, pre_checkout_query, results, data: dict):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} "
                          f"pre-checkout query [ID:{pre_checkout_query.id}] "
                          f"from user [ID:{pre_checkout_query.from_user.id}]")

    async def on_pre_process_error(self, update, error, data: dict):
        timeout = self.check_timeout(update)
        if timeout > 0:
            self.logger.info(f"Process update [ID:{update.update_id}]: [failed] (in {timeout} ms)")

    async def on_pre_process_poll(self, poll, data):
        self.logger.info(f"Received poll [ID:{poll.id}]")

    async def on_post_process_poll(self, poll, results, data):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} poll [ID:{poll.id}]")

    async def on_pre_process_poll_answer(self, poll_answer, data):
        self.logger.info(f"Received poll answer [ID:{poll_answer.poll_id}] "
                         f"from user [ID:{poll_answer.user.id}]")

    async def on_post_process_poll_answer(self, poll_answer, results, data):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} poll answer [ID:{poll_answer.poll_id}] "
                          f"from user [ID:{poll_answer.user.id}]")

    async def on_pre_process_my_chat_member(self, my_chat_member_update, data):
        self.logger.info(f"Received chat member update "
                         f"for user [ID:{my_chat_member_update.from_user.id}]. "
                         f"Old state: {my_chat_member_update.old_chat_member.to_python()} "
                         f"New state: {my_chat_member_update.new_chat_member.to_python()} ")

    async def on_post_process_my_chat_member(self, my_chat_member_update, results, data):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} my_chat_member "
                          f"for user [ID:{my_chat_member_update.from_user.id}]")

    async def on_pre_process_chat_member(self, chat_member_update, data):
        self.logger.info(f"Received chat member update "
                         f"for user [ID:{chat_member_update.from_user.id}]. "
                         f"Old state: {chat_member_update.old_chat_member.to_python()} "
                         f"New state: {chat_member_update.new_chat_member.to_python()} ")

    async def on_post_process_chat_member(self, chat_member_update, results, data):
        self.logger.debug(f"{HANDLED_STR[bool(len(results))]} chat_member "
                          f"for user [ID:{chat_member_update.from_user.id}]")


class LoggingFilter(logging.Filter):
    """
    Extend LogRecord by data from Telegram Update object.

    Can be used in logging config:
    .. code-block: python3

        'filters': {
            'telegram': {
                '()': LoggingFilter,
                'include_content': True,
            }
        },
        ...
        'handlers': {
            'graypy': {
                '()': GELFRabbitHandler,
                'url': 'amqp://localhost:5672/',
                'routing_key': '#',
                'localname': 'testapp',
                'filters': ['telegram']
            },
        },

    """

    def __init__(self, name='', prefix='tg', include_content=False):
        """
        :param name:
        :param prefix: prefix for all records
        :param include_content: pass into record all data from Update object
        """
        super(LoggingFilter, self).__init__(name=name)

        self.prefix = prefix
        self.include_content = include_content

    def filter(self, record: logging.LogRecord):
        """
        Extend LogRecord by data from Telegram Update object.

        :param record:
        :return:
        """
        update = types.Update.get_current(True)
        if update:
            for key, value in self.make_prefix(self.prefix, self.process_update(update)):
                setattr(record, key, value)

        return True

    def process_update(self, update: types.Update):
        """
        Parse Update object

        :param update:
        :return:
        """
        yield 'update_id', update.update_id

        if update.message:
            yield 'update_type', 'message'
            yield from self.process_message(update.message)
        if update.edited_message:
            yield 'update_type', 'edited_message'
            yield from self.process_message(update.edited_message)
        if update.channel_post:
            yield 'update_type', 'channel_post'
            yield from self.process_message(update.channel_post)
        if update.edited_channel_post:
            yield 'update_type', 'edited_channel_post'
            yield from self.process_message(update.edited_channel_post)
        if update.inline_query:
            yield 'update_type', 'inline_query'
            yield from self.process_inline_query(update.inline_query)
        if update.chosen_inline_result:
            yield 'update_type', 'chosen_inline_result'
            yield from self.process_chosen_inline_result(update.chosen_inline_result)
        if update.callback_query:
            yield 'update_type', 'callback_query'
            yield from self.process_callback_query(update.callback_query)
        if update.shipping_query:
            yield 'update_type', 'shipping_query'
            yield from self.process_shipping_query(update.shipping_query)
        if update.pre_checkout_query:
            yield 'update_type', 'pre_checkout_query'
            yield from self.process_pre_checkout_query(update.pre_checkout_query)

    def make_prefix(self, prefix, iterable):
        """
        Add prefix to the label

        :param prefix:
        :param iterable:
        :return:
        """
        if not prefix:
            yield from iterable

        for key, value in iterable:
            yield f"{prefix}_{key}", value

    def process_user(self, user: types.User):
        """
        Generate user data

        :param user:
        :return:
        """
        if not user:
            return

        yield 'user_id', user.id
        if self.include_content:
            yield 'user_full_name', user.full_name
            if user.username:
                yield 'user_name', f"@{user.username}"

    def process_chat(self, chat: types.Chat):
        """
        Generate chat data

        :param chat:
        :return:
        """
        if not chat:
            return

        yield 'chat_id', chat.id
        yield 'chat_type', chat.type
        if self.include_content:
            yield 'chat_title', chat.full_name
            if chat.username:
                yield 'chat_name', f"@{chat.username}"

    def process_message(self, message: types.Message):
        yield 'message_content_type', message.content_type
        yield from self.process_user(message.from_user)
        yield from self.process_chat(message.chat)

        if not self.include_content:
            return

        if message.reply_to_message:
            yield from self.make_prefix('reply_to', self.process_message(message.reply_to_message))
        if message.forward_from:
            yield from self.make_prefix('forward_from', self.process_user(message.forward_from))
        if message.forward_from_chat:
            yield from self.make_prefix('forward_from_chat', self.process_chat(message.forward_from_chat))
        if message.forward_from_message_id:
            yield 'message_forward_from_message_id', message.forward_from_message_id
        if message.forward_date:
            yield 'message_forward_date', message.forward_date
        if message.edit_date:
            yield 'message_edit_date', message.edit_date
        if message.media_group_id:
            yield 'message_media_group_id', message.media_group_id
        if message.author_signature:
            yield 'message_author_signature', message.author_signature

        if message.text:
            yield 'text', message.text or message.caption
            yield 'html_text', message.html_text
        elif message.audio:
            yield 'audio', message.audio.file_id
        elif message.animation:
            yield 'animation', message.animation.file_id
        elif message.document:
            yield 'document', message.document.file_id
        elif message.game:
            yield 'game', message.game.title
        elif message.photo:
            yield 'photo', message.photo[-1].file_id
        elif message.sticker:
            yield 'sticker', message.sticker.file_id
        elif message.video:
            yield 'video', message.video.file_id
        elif message.video_note:
            yield 'video_note', message.video_note.file_id
        elif message.voice:
            yield 'voice', message.voice.file_id
        elif message.contact:
            yield 'contact_full_name', message.contact.full_name
            yield 'contact_phone_number', message.contact.phone_number
        elif message.venue:
            yield 'venue_address', message.venue.address
            yield 'location_latitude', message.venue.location.latitude
            yield 'location_longitude', message.venue.location.longitude
        elif message.location:
            yield 'location_latitude', message.location.latitude
            yield 'location_longitude', message.location.longitude
        elif message.new_chat_members:
            yield 'new_chat_members', [user.id for user in message.new_chat_members]
        elif message.left_chat_member:
            yield 'left_chat_member', [user.id for user in message.new_chat_members]
        elif message.invoice:
            yield 'invoice_title', message.invoice.title
            yield 'invoice_description', message.invoice.description
            yield 'invoice_start_parameter', message.invoice.start_parameter
            yield 'invoice_currency', message.invoice.currency
            yield 'invoice_total_amount', message.invoice.total_amount
        elif message.successful_payment:
            yield 'successful_payment_currency', message.successful_payment.currency
            yield 'successful_payment_total_amount', message.successful_payment.total_amount
            yield 'successful_payment_invoice_payload', message.successful_payment.invoice_payload
            yield 'successful_payment_shipping_option_id', message.successful_payment.shipping_option_id
            yield 'successful_payment_telegram_payment_charge_id', message.successful_payment.telegram_payment_charge_id
            yield 'successful_payment_provider_payment_charge_id', message.successful_payment.provider_payment_charge_id
        elif message.connected_website:
            yield 'connected_website', message.connected_website
        elif message.migrate_from_chat_id:
            yield 'migrate_from_chat_id', message.migrate_from_chat_id
        elif message.migrate_to_chat_id:
            yield 'migrate_to_chat_id', message.migrate_to_chat_id
        elif message.pinned_message:
            yield from self.make_prefix('pinned_message', message.pinned_message)
        elif message.new_chat_title:
            yield 'new_chat_title', message.new_chat_title
        elif message.new_chat_photo:
            yield 'new_chat_photo', message.new_chat_photo[-1].file_id
        # elif message.delete_chat_photo:
        #     yield 'delete_chat_photo', message.delete_chat_photo
        # elif message.group_chat_created:
        #     yield 'group_chat_created', message.group_chat_created
        # elif message.passport_data:
        #     yield 'passport_data', message.passport_data

    def process_inline_query(self, inline_query: types.InlineQuery):
        yield 'inline_query_id', inline_query.id
        yield from self.process_user(inline_query.from_user)

        if self.include_content:
            yield 'inline_query_text', inline_query.query
            if inline_query.location:
                yield 'location_latitude', inline_query.location.latitude
                yield 'location_longitude', inline_query.location.longitude
            if inline_query.offset:
                yield 'inline_query_offset', inline_query.offset

    def process_chosen_inline_result(self, chosen_inline_result: types.ChosenInlineResult):
        yield 'chosen_inline_result_id', chosen_inline_result.result_id
        yield from self.process_user(chosen_inline_result.from_user)

        if self.include_content:
            yield 'inline_query_text', chosen_inline_result.query
            if chosen_inline_result.location:
                yield 'location_latitude', chosen_inline_result.location.latitude
                yield 'location_longitude', chosen_inline_result.location.longitude

    def process_callback_query(self, callback_query: types.CallbackQuery):
        yield from self.process_user(callback_query.from_user)
        yield 'callback_query_data', callback_query.data

        if callback_query.message:
            yield from self.make_prefix('callback_query_message', self.process_message(callback_query.message))
        if callback_query.inline_message_id:
            yield 'callback_query_inline_message_id', callback_query.inline_message_id
        if callback_query.chat_instance:
            yield 'callback_query_chat_instance', callback_query.chat_instance
        if callback_query.game_short_name:
            yield 'callback_query_game_short_name', callback_query.game_short_name

    def process_shipping_query(self, shipping_query: types.ShippingQuery):
        yield 'shipping_query_id', shipping_query.id
        yield from self.process_user(shipping_query.from_user)

        if self.include_content:
            yield 'shipping_query_invoice_payload', shipping_query.invoice_payload

    def process_pre_checkout_query(self, pre_checkout_query: types.PreCheckoutQuery):
        yield 'pre_checkout_query_id', pre_checkout_query.id
        yield from self.process_user(pre_checkout_query.from_user)

        if self.include_content:
            yield 'pre_checkout_query_currency', pre_checkout_query.currency
            yield 'pre_checkout_query_total_amount', pre_checkout_query.total_amount
            yield 'pre_checkout_query_invoice_payload', pre_checkout_query.invoice_payload
            yield 'pre_checkout_query_shipping_option_id', pre_checkout_query.shipping_option_id
