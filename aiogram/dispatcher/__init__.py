import asyncio
import functools
import logging
import typing

import time

from .filters import CommandsFilter, ContentTypeFilter, ExceptionsFilter, RegexpFilter, USER_STATE, \
    generate_default_filters
from .handler import Handler
from .storage import BaseStorage, DisabledStorage, FSMContext
from .webhook import BaseResponse
from ..bot import Bot
from ..types.message import ContentType
from ..utils import context
from ..utils.deprecated import deprecated
from ..utils.exceptions import NetworkError, TelegramAPIError

log = logging.getLogger(__name__)

MODE = 'MODE'
LONG_POLLING = 'long-polling'
UPDATE_OBJECT = 'update_object'


class Dispatcher:
    """
    Simple Updates dispatcher

    It will be can process incoming updates, messages, edited messages, channel posts, edited channels posts,
    inline query, chosen inline result, callback query, shipping query, pre-checkout query.
    Provide next step handler and etc.
    """

    def __init__(self, bot, loop=None, storage: typing.Optional[BaseStorage] = None,
                 run_tasks_by_default: bool = False):
        if loop is None:
            loop = bot.loop
        if storage is None:
            storage = DisabledStorage()

        self.bot: Bot = bot
        self.loop = loop
        self.storage = storage
        self.run_tasks_by_default = run_tasks_by_default

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

        self.updates_handler.register(self.process_update)

        self.errors_handlers = Handler(self, once=False)

        self._polling = False

    def __del__(self):
        self._polling = False

    @property
    def data(self):
        return self.bot.data

    def __setitem__(self, key, value):
        self.bot.data[key] = value

    def __getitem__(self, item):
        return self.bot.data[item]

    def get(self, key, default=None):
        return self.bot.data.get(key, default)

    async def skip_updates(self):
        """
        You can skip old incoming updates from queue.
        This method is not recommended to use if you use payments or you bot has high-load.

        :return: count of skipped updates
        """
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
        """
        Process list of updates

        :param updates:
        :return:
        """
        tasks = []
        for update in updates:
            tasks.append(self.process_update(update))
        return await asyncio.gather(*tasks)

    async def process_update(self, update):
        """
        Process single update object

        :param update:
        :return:
        """
        start = time.time()
        success = True

        try:
            self.last_update_id = update.update_id
            has_context = context.check_configured()
            if has_context:
                context.set_value(UPDATE_OBJECT, update)
            if update.message:
                if has_context:
                    state = await self.storage.get_state(chat=update.message.chat.id,
                                                         user=update.message.from_user.id)
                    context.update_state(chat=update.message.chat.id,
                                         user=update.message.from_user.id,
                                         state=state)
                return await self.message_handlers.notify(update.message)
            if update.edited_message:
                if has_context:
                    state = await self.storage.get_state(chat=update.edited_message.chat.id,
                                                         user=update.edited_message.from_user.id)
                    context.update_state(chat=update.edited_message.chat.id,
                                         user=update.edited_message.from_user.id,
                                         state=state)
                return await self.edited_message_handlers.notify(update.edited_message)
            if update.channel_post:
                if has_context:
                    state = await self.storage.get_state(chat=update.channel_post.chat.id)
                    context.update_state(chat=update.channel_post.chat.id,
                                         state=state)
                return await self.channel_post_handlers.notify(update.channel_post)
            if update.edited_channel_post:
                if has_context:
                    state = await self.storage.get_state(chat=update.edited_channel_post.chat.id)
                    context.update_state(chat=update.edited_channel_post.chat.id,
                                         state=state)
                return await self.edited_channel_post_handlers.notify(update.edited_channel_post)
            if update.inline_query:
                if has_context:
                    state = await self.storage.get_state(user=update.inline_query.from_user.id)
                    context.update_state(user=update.inline_query.from_user.id,
                                         state=state)
                return await self.inline_query_handlers.notify(update.inline_query)
            if update.chosen_inline_result:
                if has_context:
                    state = await self.storage.get_state(user=update.chosen_inline_result.from_user.id)
                    context.update_state(user=update.chosen_inline_result.from_user.id,
                                         state=state)
                return await self.chosen_inline_result_handlers.notify(update.chosen_inline_result)
            if update.callback_query:
                if has_context:
                    state = await self.storage.get_state(chat=update.callback_query.message.chat.id,
                                                         user=update.callback_query.from_user.id)
                    context.update_state(user=update.callback_query.from_user.id,
                                         state=state)
                return await self.callback_query_handlers.notify(update.callback_query)
            if update.shipping_query:
                if has_context:
                    state = await self.storage.get_state(user=update.shipping_query.from_user.id)
                    context.update_state(user=update.shipping_query.from_user.id,
                                         state=state)
                return await self.shipping_query_handlers.notify(update.shipping_query)
            if update.pre_checkout_query:
                if has_context:
                    state = await self.storage.get_state(user=update.pre_checkout_query.from_user.id)
                    context.update_state(user=update.pre_checkout_query.from_user.id,
                                         state=state)
                return await self.pre_checkout_query_handlers.notify(update.pre_checkout_query)
        except Exception as e:
            success = False
            err = await self.errors_handlers.notify(self, update, e)
            if err:
                return err
            raise
        finally:
            log.info(f"Process update [ID:{update.update_id}]: "
                     f"{['failed', 'success'][success]} "
                     f"(in {round((time.time() - start) * 1000)} ms)")

    async def reset_webhook(self, check=True) -> bool:
        """
        Reset webhook

        :param check: check before deleting
        :return:
        """
        if check:
            wh = await self.bot.get_webhook_info()
            if not wh.url:
                return False

        return await self.bot.delete_webhook()

    @deprecated('The old method was renamed to `start_polling`')
    async def start_pooling(self, *args, **kwargs):
        """
        Start long-lopping

        :param args:
        :param kwargs:
        :return:
        """
        return await self.start_polling(*args, **kwargs)

    async def start_polling(self, timeout=20, relax=0.1, limit=None, reset_webhook=None):
        """
        Start long-polling

        :param timeout:
        :param relax:
        :param limit:
        :param reset_webhook:
        :return:
        """
        if self._polling:
            raise RuntimeError('Polling already started')

        log.info('Start polling.')

        context.set_value(MODE, LONG_POLLING)
        context.set_value('dispatcher', self)
        context.set_value('bot', self.bot)

        if reset_webhook is None:
            await self.reset_webhook(check=False)
        if reset_webhook:
            await self.reset_webhook(check=True)

        self._polling = True
        offset = None
        while self._polling:
            try:
                updates = await self.bot.get_updates(limit=limit, offset=offset, timeout=timeout)
            except NetworkError:
                log.exception('Cause exception while getting updates.')
                await asyncio.sleep(15)
                continue

            if updates:
                log.debug(f"Received {len(updates)} updates.")
                offset = updates[-1].update_id + 1

                self.loop.create_task(self._process_polling_updates(updates))

            if relax:
                await asyncio.sleep(relax)

        log.warning('Polling is stopped.')

    async def _process_polling_updates(self, updates):
        """
        Process updates received from long-polling.

        :param updates: list of updates.
        """
        need_to_call = []
        for response in await self.process_updates(updates):
            for response in response:
                if not isinstance(response, BaseResponse):
                    continue
                need_to_call.append(response.execute_response(self.bot))
        if need_to_call:
            try:
                asyncio.gather(*need_to_call)
            except TelegramAPIError:
                log.exception('Cause exception while processing updates.')

    @deprecated('The old method was renamed to `stop_polling`')
    def stop_pooling(self):
        return self.stop_polling()

    def stop_polling(self):
        """
        Break long-polling process.
        :return:
        """
        if self._polling:
            log.info('Stop polling.')
            self._polling = False

    @deprecated('The old method was renamed to `is_polling`')
    def is_pooling(self):
        return self.is_polling()

    def is_polling(self):
        """
        Check polling is enabled?

        :return:
        """
        return self._polling

    def register_message_handler(self, callback, *, commands=None, regexp=None, content_types=None, func=None,
                                 state=None, custom_filters=None, run_task=None, **kwargs):
        """
        You can register messages handler by this method

        .. code-block:: python3

            # This handler works only is state is None (by default).
            dp.register_message_handler(cmd_start, commands=['start', 'about'])
            dp.register_message_handler(entry_point, commands=['setup'])

            # That handler works only if current state is "first_step"
            dp.register_message_handler(step_handler_1, state="first_step")

            # If you want to handle all states by one handler then use state="*".
            dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
            dp.register_message_handler(cancel_handler, func=lambda msg: msg.text.lower() == 'cancel', state="*")

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param custom_filters: list of custom filters
        :param kwargs:
        :param state:
        :return: decorated function
        """
        if content_types is None:
            content_types = ContentType.TEXT
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.message_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def message_handler(self, *custom_filters, commands=None, regexp=None, content_types=None, func=None, state=None,
                        run_task=None, **kwargs):
        """
        Decorator for messages handler

        Examples:

        Simple commands handler:

        .. code-block:: python3

            @dp.messages_handler(commands=['start', 'welcome', 'about'])
            async def cmd_handler(message: types.Message):

        Filter messages by regular expression:

        .. code-block:: python3

            @dp.messages_handler(rexexp='^[a-z]+-[0-9]+')
            async def msg_handler(message: types.Message):

        Filter by content type:

        .. code-block:: python3

            @dp.messages_handler(content_types=ContentType.PHOTO | ContentType.DOCUMENT)
            async def audio_handler(message: types.Message):

        Filter by custom function:

        .. code-block:: python3

            @dp.messages_handler(func=lambda message: message.text and 'hello' in message.text.lower())
            async def text_handler(message: types.Message):

        Use multiple filters:

        .. code-block:: python3

            @dp.messages_handler(commands=['command'], content_types=ContentType.TEXT)
            async def text_handler(message: types.Message):

        Register multiple filters set for one handler:

        .. code-block:: python3

            @dp.messages_handler(commands=['command'])
            @dp.messages_handler(func=lambda message: demojize(message.text) == ':new_moon_with_face:')
            async def text_handler(message: types.Message):

        This handler will be called if the message starts with '/command' OR is some emoji

        By default content_type is :class:`ContentType.TEXT`

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param custom_filters: list of custom filters
        :param kwargs:
        :param state:
        :param run_task: run callback in task (no wait results)
        :return: decorated function
        """

        def decorator(callback):
            self.register_message_handler(callback,
                                          commands=commands, regexp=regexp, content_types=content_types,
                                          func=func, state=state, custom_filters=custom_filters, run_task=run_task,
                                          **kwargs)
            return callback

        return decorator

    def register_edited_message_handler(self, callback, *, commands=None, regexp=None, content_types=None, func=None,
                                        state=None, custom_filters=None, run_task=None, **kwargs):
        """
        Analog of message_handler but only for edited messages

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        if commands is None:
            commands = []
        if content_types is None:
            content_types = ContentType.TEXT
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.edited_message_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def edited_message_handler(self, *custom_filters, commands=None, regexp=None, content_types=None, func=None,
                               state=None, run_task=None, **kwargs):
        """
        Analog of message_handler but only for edited messages

        You can use combination of different handlers

        .. code-block:: python3

            @dp.message_handler()
            @dp.edited_message_handler()
            async def msg_handler(message: types.Message):

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_edited_message_handler(callback, commands=commands, regexp=regexp,
                                                 content_types=content_types, func=func, state=state,
                                                 custom_filters=custom_filters, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_channel_post_handler(self, callback, *, commands=None, regexp=None, content_types=None, func=None,
                                      state=None, custom_filters=None, run_task=None, **kwargs):
        """
        Register channels posts handler

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        if commands is None:
            commands = []
        if content_types is None:
            content_types = ContentType.TEXT
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.channel_post_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def channel_post_handler(self, *custom_filters, commands=None, regexp=None, content_types=None, func=None,
                             state=None, run_task=None, **kwargs):
        """
        Register channels posts handler

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_channel_post_handler(callback, commands=commands, regexp=regexp, content_types=content_types,
                                               func=func, state=state, custom_filters=custom_filters,
                                               run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_edited_channel_post_handler(self, callback, *, commands=None, regexp=None, content_types=None,
                                             func=None, state=None, custom_filters=None, run_task=None, **kwargs):
        """
        Register handler for edited channels posts

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        if commands is None:
            commands = []
        if content_types is None:
            content_types = ContentType.TEXT
        if custom_filters is None:
            custom_filters = []

        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               commands=commands,
                                               regexp=regexp,
                                               content_types=content_types,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.edited_channel_post_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def edited_channel_post_handler(self, *custom_filters, commands=None, regexp=None, content_types=None, func=None,
                                    state=None, run_task=None, **kwargs):
        """
        Register handler for edited channels posts

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param custom_filters: list of custom filters
        :param state:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_edited_channel_post_handler(callback, commands=commands, regexp=regexp,
                                                      content_types=content_types, func=func, state=state,
                                                      custom_filters=custom_filters, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_inline_handler(self, callback, *, func=None, state=None, custom_filters=None, run_task=None, **kwargs):
        """
        Handle inline query

        Example:

        .. code-block:: python3

            @dp.inline_handler(func=lambda inline_query: True)
            async def handler(inline_query: types.InlineQuery)

        :param callback:
        :param func: custom any callable object
        :param custom_filters: list of custom filters
        :param state:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.inline_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def inline_handler(self, *custom_filters, func=None, state=None, run_task=None, **kwargs):
        """
        Handle inline query

        Example:

        .. code-block:: python3

            @dp.inline_handler(func=lambda inline_query: True)
            async def handler(inline_query: types.InlineQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_inline_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                         run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_chosen_inline_handler(self, callback, *, func=None, state=None, custom_filters=None, run_task=None,
                                       **kwargs):
        """
        Register chosen inline handler

        Example:

        .. code-block:: python3

            @dp.chosen_inline_handler(func=lambda chosen_inline_query: True)
            async def handler(chosen_inline_query: types.ChosenInlineResult)

        :param callback:
        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.chosen_inline_result_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def chosen_inline_handler(self, *custom_filters, func=None, state=None, run_task=None, **kwargs):
        """
        Register chosen inline handler

        Example:

        .. code-block:: python3

            @dp.chosen_inline_handler(func=lambda chosen_inline_query: True)
            async def handler(chosen_inline_query: types.ChosenInlineResult)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return:
        """

        def decorator(callback):
            self.register_chosen_inline_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_callback_query_handler(self, callback, *, func=None, state=None, custom_filters=None, run_task=None,
                                        **kwargs):
        """
        Add callback query handler

        Example:

        .. code-block:: python3

            @dp.callback_query_handler(func=lambda callback_query: True)
            async def handler(callback_query: types.CallbackQuery)

        :param callback:
        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.callback_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def callback_query_handler(self, *custom_filters, func=None, state=None, run_task=None, **kwargs):
        """
        Add callback query handler

        Example:

        .. code-block:: python3

            @dp.callback_query_handler(func=lambda callback_query: True)
            async def handler(callback_query: types.CallbackQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_callback_query_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                 run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_shipping_query_handler(self, callback, *, func=None, state=None, custom_filters=None, run_task=None,
                                        **kwargs):
        """
        Add shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(func=lambda shipping_query: True)
            async def handler(shipping_query: types.ShippingQuery)

        :param callback:
        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.shipping_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def shipping_query_handler(self, *custom_filters, func=None, state=None, run_task=None, **kwargs):
        """
        Add shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(func=lambda shipping_query: True)
            async def handler(shipping_query: types.ShippingQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_shipping_query_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                 run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_pre_checkout_query_handler(self, callback, *, func=None, state=None, custom_filters=None,
                                            run_task=None, **kwargs):
        """
        Add shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(func=lambda shipping_query: True)
            async def handler(shipping_query: types.ShippingQuery)

        :param callback:
        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.pre_checkout_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def pre_checkout_query_handler(self, *custom_filters, func=None, state=None, run_task=None, **kwargs):
        """
        Add shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(func=lambda shipping_query: True)
            async def handler(shipping_query: types.ShippingQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_pre_checkout_query_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                     run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_errors_handler(self, callback, *, func=None, exception=None, run_task=None):
        """
        Register errors handler

        :param callback:
        :param func:
        :param exception: you can make handler for specific errors type
        :param run_task: run callback in task (no wait results)
        """
        filters_set = []
        if func is not None:
            filters_set.append(func)
        if exception is not None:
            filters_set.append(ExceptionsFilter(exception))
        self.errors_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def errors_handler(self, func=None, exception=None, run_task=None):
        """
        Decorator for registering errors handler

        :param func:
        :param exception: you can make handler for specific errors type
        :param run_task: run callback in task (no wait results)
        :return:
        """

        def decorator(callback):
            self.register_errors_handler(callback, func=func, exception=exception)
            return callback

        return decorator

    def current_state(self, *,
                      chat: typing.Union[str, int, None] = None,
                      user: typing.Union[str, int, None] = None) -> FSMContext:
        """
        Get current state for user in chat as context

        .. code-block:: python3

            with dp.current_state(chat=message.chat.id, user=message.user.id) as state:
                pass

            state = dp.current_state()
            state.set_state('my_state')

        :param chat:
        :param user:
        :return:
        """
        if chat is None:
            from .ctx import get_chat
            chat = get_chat()
        if user is None:
            from .ctx import get_user
            user = get_user()

        return FSMContext(storage=self.storage, chat=chat, user=user)

    def async_task(self, func):
        """
        Execute handler as task and return None.
        Use that decorator for slow handlers (with timeouts)

        .. code-block:: python3

            @dp.message_handler(commands=['command'])
            @dp.async_task
            async def cmd_with_timeout(message: types.Message):
                await asyncio.sleep(120)
                return SendMessage(message.chat.id, 'KABOOM').reply(message)

        :param func:
        :return:
        """

        def process_response(task):
            response = task.result()

            if isinstance(response, BaseResponse):
                self.loop.create_task(response.execute_response(self.bot))

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            task = self.loop.create_task(func(*args, **kwargs))
            task.add_done_callback(process_response)

        return wrapper

    def _wrap_async_task(self, callback, run_task=None) -> callable:
        if run_task is None:
            run_task = self.run_tasks_by_default

        if run_task:
            return self.async_task(callback)
        return callback
