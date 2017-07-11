import asyncio
import logging

from .filters import CommandsFilter, RegexpFilter, ContentTypeFilter, generate_default_filters
from .handler import Handler, NextStepHandler
from .. import types
from ..bot import Bot
from ..types.message import ContentType

log = logging.getLogger(__name__)


class Dispatcher:
    def __init__(self, bot, loop=None):
        self.bot: 'Bot' = bot
        if loop is None:
            loop = self.bot.loop

        self.loop = loop

        self.last_update_id = 0

        self.updates_handler = Handler(self)
        self.message_handlers = Handler(self)
        self.edited_message_handlers = Handler(self)
        self.channel_post_handlers = Handler(self)
        self.edited_channel_post_handlers = Handler(self)
        self.inline_query_handlers = Handler(self)
        self.chosen_inline_result_handlers = Handler(self)
        self.callback_query_handlers = Handler(self)
        self.shipping_query_handlers = Handler(self)
        self.pre_checkout_query_handlers = Handler(self)

        self.next_step_message_handlers = NextStepHandler(self)
        self.updates_handler.register(self.process_update)
        # self.message_handlers.register(self._notify_next_message)

        self._pooling = False

    def __del__(self):
        self._pooling = False

    async def skip_updates(self):
        total = 0
        updates = await self.bot.get_updates(offset=self.last_update_id, timeout=1)
        while updates:
            total += len(updates)
            for update in updates:
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
            updates = await self.bot.get_updates(offset=self.last_update_id + 1, timeout=1)
        return total

    async def process_updates(self, updates):
        for update in updates:
            self.loop.create_task(self.updates_handler.notify(update))

    async def process_update(self, update):
        self.last_update_id = update.update_id
        if update.message:
            if not await self.next_step_message_handlers.notify(update.message):
                await self.message_handlers.notify(update.message)
        if update.edited_message:
            await self.edited_message_handlers.notify(update.edited_message)
        if update.channel_post:
            await self.channel_post_handlers.notify(update.channel_post)
        if update.edited_channel_post:
            await self.edited_channel_post_handlers.notify(update.edited_channel_post)
        if update.inline_query:
            await self.inline_query_handlers.notify(update.inline_query)
        if update.chosen_inline_result:
            await self.chosen_inline_result_handlers.notify(update.chosen_inline_result)
        if update.callback_query:
            await self.callback_query_handlers.notify(update.callback_query)
        if update.shipping_query:
            await self.shipping_query_handlers.notify(update.shipping_query)
        if update.pre_checkout_query:
            await self.pre_checkout_query_handlers.notify(update.pre_checkout_query)

    async def start_pooling(self, timeout=20, relax=0.1):
        if self._pooling:
            raise RuntimeError('Pooling already started')
        log.info('Start pooling.')

        self._pooling = True
        offset = None
        while self._pooling:
            try:
                updates = await self.bot.get_updates(offset=offset, timeout=timeout)
            except Exception as e:
                log.exception('Cause exception while getting updates')
                await asyncio.sleep(relax)
                continue

            if updates:
                log.info(f"Received {len(updates)} updates.")
                offset = updates[-1].update_id + 1
                await self.process_updates(updates)

            await asyncio.sleep(relax)

        log.warning('Pooling is stopped.')

    def stop_pooling(self):
        self._pooling = False

    def message_handler(self, commands=None, regexp=None, content_types=None, func=None, custom_filters=None, **kwargs):
        if commands is None:
            commands = []
        if content_types is None:
            content_types = [ContentType.TEXT]
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(*custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.message_handlers.register(func, filters_set)
            return func

        return decorator

    def edited_message_handler(self, commands=None, regexp=None, content_types=None, func=None, custom_filters=None,
                               **kwargs):
        if commands is None:
            commands = []
        if content_types is None:
            content_types = [ContentType.TEXT]
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(*custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.edited_message_handlers.register(func, filters_set)
            return func

        return decorator

    def channel_post_handler(self, commands=None, regexp=None, content_types=None, func=None, *custom_filters, **kwargs):
        if commands is None:
            commands = []
        if content_types is None:
            content_types = [ContentType.TEXT]
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(*custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.channel_post_handlers.register(func, filters_set)
            return func

        return decorator

    def edited_channel_post_handler(self, commands=None, regexp=None, content_types=None, func=None, *custom_filters,
                                    **kwargs):
        if commands is None:
            commands = []
        if content_types is None:
            content_types = [ContentType.TEXT]
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(*custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.edited_channel_post_handlers.register(func, filters_set)
            return func

        return decorator

    def inline_handler(self, func=None, *custom_filters, **kwargs):
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(*custom_filters,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.inline_query_handlers.register(func, filters_set)
            return func

        return decorator

    def chosen_inline_handler(self, func=None, *custom_filters, **kwargs):
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(*custom_filters,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.chosen_inline_result_handlers.register(func, filters_set)
            return func

        return decorator

    def callback_query_handler(self, func=None, *custom_filters, **kwargs):
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(*custom_filters,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.chosen_inline_result_handlers.register(func, filters_set)
            return func

        return decorator

    def shipping_query_handler(self, func=None, *custom_filters, **kwargs):
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(*custom_filters,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.shipping_query_handlers.register(func, filters_set)
            return func

        return decorator

    def pre_checkout_query_handler(self, func=None, *custom_filters, **kwargs):
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(*custom_filters,
                                               func=func,
                                               **kwargs)

        def decorator(func):
            self.pre_checkout_query_handlers.register(func, filters_set)
            return func

        return decorator

    async def next_message(self, message: types.Message, otherwise=None, once=False, include_cancel=True,
                           regexp=None, content_types=None, func=None, custom_filters=None, **kwargs):
        if content_types is None:
            content_types = []
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(*custom_filters,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               **kwargs)
        self.next_step_message_handlers.register(message, otherwise, once, include_cancel, filters_set)
        return await self.next_step_message_handlers.wait(message)
