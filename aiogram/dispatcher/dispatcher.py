import asyncio
import functools
import itertools
import logging
import time
import typing

import aiohttp
from aiohttp.helpers import sentinel

from aiogram.utils.deprecated import renamed_argument
from .filters import Command, ContentTypeFilter, ExceptionsFilter, FiltersFactory, HashTag, Regexp, \
    RegexpCommandsFilter, StateFilter, Text, IDFilter, AdminFilter, IsReplyFilter, ForwardedMessageFilter, \
    IsSenderContact, ChatTypeFilter, AbstractFilter
from .handler import Handler
from .middlewares import MiddlewareManager
from .storage import BaseStorage, DELTA, DisabledStorage, EXCEEDED_COUNT, FSMContext, \
    LAST_CALL, RATE_LIMIT, RESULT
from .webhook import BaseResponse
from .. import types
from ..bot import Bot
from ..utils.exceptions import TelegramAPIError, Throttled
from ..utils.mixins import ContextInstanceMixin, DataMixin

log = logging.getLogger(__name__)

DEFAULT_RATE_LIMIT = .1


def _ensure_loop(x: "asyncio.AbstractEventLoop"):
    assert isinstance(
        x, asyncio.AbstractEventLoop
    ), f"Loop must be the implementation of {asyncio.AbstractEventLoop!r}, " \
       f"not {type(x)!r}"


class Dispatcher(DataMixin, ContextInstanceMixin):
    """
    Simple Updates dispatcher

    It will process incoming updates: messages, edited messages, channel posts, edited channel posts,
    inline queries, chosen inline results, callback queries, shipping queries, pre-checkout queries.
    """

    def __init__(self, bot, loop=None, storage: typing.Optional[BaseStorage] = None,
                 run_tasks_by_default: bool = False,
                 throttling_rate_limit=DEFAULT_RATE_LIMIT, no_throttle_error=False,
                 filters_factory=None):

        if not isinstance(bot, Bot):
            raise TypeError(f"Argument 'bot' must be an instance of Bot, not '{type(bot).__name__}'")

        if storage is None:
            storage = DisabledStorage()
        if filters_factory is None:
            filters_factory = FiltersFactory(self)

        self.bot: Bot = bot
        if loop is not None:
            _ensure_loop(loop)
        self._main_loop = loop
        self.storage = storage
        self.run_tasks_by_default = run_tasks_by_default

        self.throttling_rate_limit = throttling_rate_limit
        self.no_throttle_error = no_throttle_error

        self.filters_factory: FiltersFactory = filters_factory
        self.updates_handler = Handler(self, middleware_key='update')
        self.message_handlers = Handler(self, middleware_key='message')
        self.edited_message_handlers = Handler(self, middleware_key='edited_message')
        self.channel_post_handlers = Handler(self, middleware_key='channel_post')
        self.edited_channel_post_handlers = Handler(self, middleware_key='edited_channel_post')
        self.inline_query_handlers = Handler(self, middleware_key='inline_query')
        self.chosen_inline_result_handlers = Handler(self, middleware_key='chosen_inline_result')
        self.callback_query_handlers = Handler(self, middleware_key='callback_query')
        self.shipping_query_handlers = Handler(self, middleware_key='shipping_query')
        self.pre_checkout_query_handlers = Handler(self, middleware_key='pre_checkout_query')
        self.poll_handlers = Handler(self, middleware_key='poll')
        self.poll_answer_handlers = Handler(self, middleware_key='poll_answer')
        self.errors_handlers = Handler(self, once=False, middleware_key='error')

        self.middleware = MiddlewareManager(self)

        self.updates_handler.register(self.process_update)

        self._polling = False
        self._closed = True
        self._dispatcher_close_waiter = None

        self._setup_filters()

    @property
    def loop(self) -> typing.Optional[asyncio.AbstractEventLoop]:
        # for the sake of backward compatibility
        # lib internally must delegate tasks with respect to _main_loop attribute
        # however should never be used by the library itself
        # use more generic approaches from asyncio's namespace
        return self._main_loop

    @property
    def _close_waiter(self) -> "asyncio.Future":
        if self._dispatcher_close_waiter is None:
            if self._main_loop is not None:
                self._dispatcher_close_waiter = self._main_loop.create_future()
            else:
                self._dispatcher_close_waiter = asyncio.get_event_loop().create_future()
        return self._dispatcher_close_waiter

    def _setup_filters(self):
        filters_factory = self.filters_factory

        filters_factory.bind(StateFilter, exclude_event_handlers=[
            self.errors_handlers,
            self.poll_handlers,
            self.poll_answer_handlers,
        ])
        filters_factory.bind(ContentTypeFilter, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
        ]),
        filters_factory.bind(Command, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers
        ])
        filters_factory.bind(Text, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
            self.callback_query_handlers,
            self.poll_handlers,
            self.inline_query_handlers,
        ])
        filters_factory.bind(HashTag, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
        ])
        filters_factory.bind(Regexp, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
            self.callback_query_handlers,
            self.poll_handlers,
            self.inline_query_handlers,
        ])
        filters_factory.bind(RegexpCommandsFilter, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
        ])
        filters_factory.bind(ExceptionsFilter, event_handlers=[
            self.errors_handlers,
        ])
        filters_factory.bind(AdminFilter, event_handlers=[
            self.message_handlers, 
            self.edited_message_handlers,
            self.channel_post_handlers, 
            self.edited_channel_post_handlers,
            self.callback_query_handlers, 
            self.inline_query_handlers,
        ])
        filters_factory.bind(IDFilter, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
            self.callback_query_handlers,
            self.inline_query_handlers,
        ])
        filters_factory.bind(IsReplyFilter, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
        ])
        filters_factory.bind(IsSenderContact, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
        ])
        filters_factory.bind(ForwardedMessageFilter, event_handlers=[
            self.message_handlers,
            self.edited_channel_post_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers
        ])
        filters_factory.bind(ChatTypeFilter, event_handlers=[
            self.message_handlers,
            self.edited_message_handlers,
            self.channel_post_handlers,
            self.edited_channel_post_handlers,
            self.callback_query_handlers,
        ])

    def __del__(self):
        self.stop_polling()

    async def skip_updates(self):
        """
        You can skip old incoming updates from queue.
        This method is not recommended to use if you use payments or you bot has high-load.

        :return: None
        """
        await self.bot.get_updates(offset=-1, timeout=1)

    async def process_updates(self, updates, fast: typing.Optional[bool] = True):
        """
        Process list of updates

        :param updates:
        :param fast:
        :return:
        """
        if fast:
            tasks = []
            for update in updates:
                tasks.append(self.updates_handler.notify(update))
            return await asyncio.gather(*tasks)

        results = []
        for update in updates:
            results.append(await self.updates_handler.notify(update))
        return results

    async def process_update(self, update: types.Update):
        """
        Process single update object

        :param update:
        :return:
        """
        types.Update.set_current(update)

        try:
            if update.message:
                types.Message.set_current(update.message)
                types.User.set_current(update.message.from_user)
                types.Chat.set_current(update.message.chat)
                return await self.message_handlers.notify(update.message)
            if update.edited_message:
                types.Message.set_current(update.edited_message)
                types.User.set_current(update.edited_message.from_user)
                types.Chat.set_current(update.edited_message.chat)
                return await self.edited_message_handlers.notify(update.edited_message)
            if update.channel_post:
                types.Message.set_current(update.channel_post)
                types.Chat.set_current(update.channel_post.chat)
                return await self.channel_post_handlers.notify(update.channel_post)
            if update.edited_channel_post:
                types.Message.set_current(update.edited_channel_post)
                types.Chat.set_current(update.edited_channel_post.chat)
                return await self.edited_channel_post_handlers.notify(update.edited_channel_post)
            if update.inline_query:
                types.InlineQuery.set_current(update.inline_query)
                types.User.set_current(update.inline_query.from_user)
                return await self.inline_query_handlers.notify(update.inline_query)
            if update.chosen_inline_result:
                types.ChosenInlineResult.set_current(update.chosen_inline_result)
                types.User.set_current(update.chosen_inline_result.from_user)
                return await self.chosen_inline_result_handlers.notify(update.chosen_inline_result)
            if update.callback_query:
                types.CallbackQuery.set_current(update.callback_query)
                if update.callback_query.message:
                    types.Chat.set_current(update.callback_query.message.chat)
                types.User.set_current(update.callback_query.from_user)
                return await self.callback_query_handlers.notify(update.callback_query)
            if update.shipping_query:
                types.ShippingQuery.set_current(update.shipping_query)
                types.User.set_current(update.shipping_query.from_user)
                return await self.shipping_query_handlers.notify(update.shipping_query)
            if update.pre_checkout_query:
                types.PreCheckoutQuery.set_current(update.pre_checkout_query)
                types.User.set_current(update.pre_checkout_query.from_user)
                return await self.pre_checkout_query_handlers.notify(update.pre_checkout_query)
            if update.poll:
                types.Poll.set_current(update.poll)
                return await self.poll_handlers.notify(update.poll)
            if update.poll_answer:
                types.PollAnswer.set_current(update.poll_answer)
                types.User.set_current(update.poll_answer.user)
                return await self.poll_answer_handlers.notify(update.poll_answer)
        except Exception as e:
            err = await self.errors_handlers.notify(update, e)
            if err:
                return err
            raise

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

    def _loop_create_task(self, coro):
        if self._main_loop is None:
            return asyncio.create_task(coro)
        else:
            _ensure_loop(self._main_loop)
            return self._main_loop.create_task(coro)

    async def start_polling(self,
                            timeout=20,
                            relax=0.1,
                            limit=None,
                            reset_webhook=None,
                            fast: typing.Optional[bool] = True,
                            error_sleep: int = 5):
        """
        Start long-polling

        :param timeout:
        :param relax:
        :param limit:
        :param reset_webhook:
        :param fast:
        :return:
        """
        if self._polling:
            raise RuntimeError('Polling already started')

        log.info('Start polling.')

        # context.set_value(MODE, LONG_POLLING)
        Dispatcher.set_current(self)
        Bot.set_current(self.bot)

        if reset_webhook is None:
            await self.reset_webhook(check=False)
        if reset_webhook:
            await self.reset_webhook(check=True)

        self._polling = True
        offset = None
        try:
            current_request_timeout = self.bot.timeout
            if current_request_timeout is not sentinel and timeout is not None:
                request_timeout = aiohttp.ClientTimeout(total=current_request_timeout.total + timeout or 1)
            else:
                request_timeout = None

            while self._polling:
                try:
                    with self.bot.request_timeout(request_timeout):
                        updates = await self.bot.get_updates(limit=limit, offset=offset, timeout=timeout)
                except asyncio.CancelledError:
                    break
                except:
                    log.exception('Cause exception while getting updates.')
                    await asyncio.sleep(error_sleep)
                    continue

                if updates:
                    log.debug(f"Received {len(updates)} updates.")
                    offset = updates[-1].update_id + 1

                    self._loop_create_task(self._process_polling_updates(updates, fast))

                if relax:
                    await asyncio.sleep(relax)

        finally:
            self._close_waiter.set_result(None)
            log.warning('Polling is stopped.')

    async def _process_polling_updates(self, updates, fast: typing.Optional[bool] = True):
        """
        Process updates received from long-polling.

        :param updates: list of updates.
        :param fast:
        """
        need_to_call = []
        for responses in itertools.chain.from_iterable(await self.process_updates(updates, fast)):
            for response in responses:
                if not isinstance(response, BaseResponse):
                    continue
                need_to_call.append(response.execute_response(self.bot))
        if need_to_call:
            try:
                asyncio.gather(*need_to_call)
            except TelegramAPIError:
                log.exception('Cause exception while processing updates.')

    def stop_polling(self):
        """
        Break long-polling process.

        :return:
        """
        if hasattr(self, '_polling') and self._polling:
            log.info('Stop polling...')
            self._polling = False

    async def wait_closed(self):
        """
        Wait for the long-polling to close

        :return:
        """
        await asyncio.shield(self._close_waiter)

    def is_polling(self):
        """
        Check if polling is enabled

        :return:
        """
        return self._polling

    def register_message_handler(self, callback, *custom_filters, commands=None, regexp=None, content_types=None,
                                 state=None, run_task=None, **kwargs):
        """
        Register handler for message

        .. code-block:: python3

            # This handler works only if state is None (by default).
            dp.register_message_handler(cmd_start, commands=['start', 'about'])
            dp.register_message_handler(entry_point, commands=['setup'])

            # This handler works only if current state is "first_step"
            dp.register_message_handler(step_handler_1, state="first_step")

            # If you want to handle all states by one handler, use `state="*"`.
            dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
            dp.register_message_handler(cancel_handler, lambda msg: msg.text.lower() == 'cancel', state="*")

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param custom_filters: list of custom filters
        :param kwargs:
        :param state:
        :return: decorated function
        """
        filters_set = self.filters_factory.resolve(self.message_handlers,
                                                   *custom_filters,
                                                   commands=commands,
                                                   regexp=regexp,
                                                   content_types=content_types,
                                                   state=state,
                                                   **kwargs)
        self.message_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def message_handler(self, *custom_filters, commands=None, regexp=None, content_types=None, state=None,
                        run_task=None, **kwargs):
        """
        Decorator for message handler

        Examples:

        Simple commands handler:

        .. code-block:: python3

            @dp.message_handler(commands=['start', 'welcome', 'about'])
            async def cmd_handler(message: types.Message):

        Filter messages by regular expression:

        .. code-block:: python3

            @dp.message_handler(regexp='^[a-z]+-[0-9]+')
            async def msg_handler(message: types.Message):

        Filter messages by command regular expression:

        .. code-block:: python3

            @dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['item_([0-9]*)']))
            async def send_welcome(message: types.Message):

        Filter by content type:

        .. code-block:: python3

            @dp.message_handler(content_types=ContentType.PHOTO | ContentType.DOCUMENT)
            async def audio_handler(message: types.Message):

        Filter by custom function:

        .. code-block:: python3

            @dp.message_handler(lambda message: message.text and 'hello' in message.text.lower())
            async def text_handler(message: types.Message):

        Use multiple filters:

        .. code-block:: python3

            @dp.message_handler(commands=['command'], content_types=ContentType.TEXT)
            async def text_handler(message: types.Message):

        Register multiple filters set for one handler:

        .. code-block:: python3

            @dp.message_handler(commands=['command'])
            @dp.message_handler(lambda message: demojize(message.text) == ':new_moon_with_face:')
            async def text_handler(message: types.Message):

        This handler will be called if the message starts with '/command' OR is some emoji

        By default content_type is :class:`ContentType.TEXT`

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param custom_filters: list of custom filters
        :param kwargs:
        :param state:
        :param run_task: run callback in task (no wait results)
        :return: decorated function
        """

        def decorator(callback):
            self.register_message_handler(callback, *custom_filters,
                                          commands=commands, regexp=regexp, content_types=content_types,
                                          state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_edited_message_handler(self, callback, *custom_filters, commands=None, regexp=None, content_types=None,
                                        state=None, run_task=None, **kwargs):
        """
        Register handler for edited message

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        filters_set = self.filters_factory.resolve(self.edited_message_handlers,
                                                   *custom_filters,
                                                   commands=commands,
                                                   regexp=regexp,
                                                   content_types=content_types,
                                                   state=state,
                                                   **kwargs)
        self.edited_message_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def edited_message_handler(self, *custom_filters, commands=None, regexp=None, content_types=None,
                               state=None, run_task=None, **kwargs):
        """
        Decorator for edited message handler

        You can use combination of different handlers

        .. code-block:: python3

            @dp.message_handler()
            @dp.edited_message_handler()
            async def msg_handler(message: types.Message):

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_edited_message_handler(callback, *custom_filters, commands=commands, regexp=regexp,
                                                 content_types=content_types, state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_channel_post_handler(self, callback, *custom_filters, commands=None, regexp=None, content_types=None,
                                      state=None, run_task=None, **kwargs):
        """
        Register handler for channel post

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        filters_set = self.filters_factory.resolve(self.channel_post_handlers,
                                                   *custom_filters,
                                                   commands=commands,
                                                   regexp=regexp,
                                                   content_types=content_types,
                                                   state=state,
                                                   **kwargs)
        self.channel_post_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def channel_post_handler(self, *custom_filters, commands=None, regexp=None, content_types=None,
                             state=None, run_task=None, **kwargs):
        """
        Decorator for channel post handler

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_channel_post_handler(callback, *custom_filters, commands=commands, regexp=regexp,
                                               content_types=content_types, state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_edited_channel_post_handler(self, callback, *custom_filters, commands=None, regexp=None,
                                             content_types=None, state=None, run_task=None, **kwargs):
        """
        Register handler for edited channel post

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        filters_set = self.filters_factory.resolve(self.edited_message_handlers,
                                                   *custom_filters,
                                                   commands=commands,
                                                   regexp=regexp,
                                                   content_types=content_types,
                                                   state=state,
                                                   **kwargs)
        self.edited_channel_post_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def edited_channel_post_handler(self, *custom_filters, commands=None, regexp=None, content_types=None,
                                    state=None, run_task=None, **kwargs):
        """
        Decorator for edited channel post handler

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param custom_filters: list of custom filters
        :param state:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_edited_channel_post_handler(callback, *custom_filters, commands=commands, regexp=regexp,
                                                      content_types=content_types, state=state, run_task=run_task,
                                                      **kwargs)
            return callback

        return decorator

    def register_inline_handler(self, callback, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Register handler for inline query

        Example:

        .. code-block:: python3

            dp.register_inline_handler(some_inline_handler, lambda inline_query: True)

        :param callback:
        :param custom_filters: list of custom filters
        :param state:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = self.filters_factory.resolve(self.inline_query_handlers,
                                                   *custom_filters,
                                                   state=state,
                                                   **kwargs)
        self.inline_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def inline_handler(self, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Decorator for inline query handler

        Example:

        .. code-block:: python3

            @dp.inline_handler(lambda inline_query: True)
            async def some_inline_handler(inline_query: types.InlineQuery)

        :param state:
        :param custom_filters: list of custom filters
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_inline_handler(callback, *custom_filters, state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_chosen_inline_handler(self, callback, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Register handler for chosen inline query

        Example:

        .. code-block:: python3

            dp.register_chosen_inline_handler(some_chosen_inline_handler, lambda chosen_inline_query: True)

        :param callback:
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = self.filters_factory.resolve(self.chosen_inline_result_handlers,
                                                   *custom_filters,
                                                   state=state,
                                                   **kwargs)
        self.chosen_inline_result_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def chosen_inline_handler(self, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Decorator for chosen inline query handler

        Example:

        .. code-block:: python3

            @dp.chosen_inline_handler(lambda chosen_inline_query: True)
            async def some_chosen_inline_handler(chosen_inline_query: types.ChosenInlineResult)

        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        :return:
        """

        def decorator(callback):
            self.register_chosen_inline_handler(callback, *custom_filters, state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_callback_query_handler(self, callback, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Register handler for callback query

        Example:

        .. code-block:: python3

            dp.register_callback_query_handler(some_callback_handler, lambda callback_query: True)

        :param callback:
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        filters_set = self.filters_factory.resolve(self.callback_query_handlers,
                                                   *custom_filters,
                                                   state=state,
                                                   **kwargs)
        self.callback_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def callback_query_handler(self, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Decorator for callback query handler

        Example:

        .. code-block:: python3

            @dp.callback_query_handler(lambda callback_query: True)
            async def some_callback_handler(callback_query: types.CallbackQuery)

        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_callback_query_handler(callback, *custom_filters, state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_shipping_query_handler(self, callback, *custom_filters, state=None, run_task=None,
                                        **kwargs):
        """
        Register handler for shipping query

        Example:

        .. code-block:: python3

            dp.register_shipping_query_handler(some_shipping_query_handler, lambda shipping_query: True)

        :param callback:
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        filters_set = self.filters_factory.resolve(self.shipping_query_handlers,
                                                   *custom_filters,
                                                   state=state,
                                                   **kwargs)
        self.shipping_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def shipping_query_handler(self, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Decorator for shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(lambda shipping_query: True)
            async def some_shipping_query_handler(shipping_query: types.ShippingQuery)

        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_shipping_query_handler(callback, *custom_filters, state=state, run_task=run_task, **kwargs)
            return callback

        return decorator

    def register_pre_checkout_query_handler(self, callback, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Register handler for pre-checkout query

        Example:

        .. code-block:: python3

            dp.register_pre_checkout_query_handler(some_pre_checkout_query_handler, lambda shipping_query: True)

        :param callback:
        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        filters_set = self.filters_factory.resolve(self.pre_checkout_query_handlers,
                                                   *custom_filters,
                                                   state=state,
                                                   **kwargs)
        self.pre_checkout_query_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def pre_checkout_query_handler(self, *custom_filters, state=None, run_task=None, **kwargs):
        """
        Decorator for pre-checkout query handler

        Example:

        .. code-block:: python3

            @dp.pre_checkout_query_handler(lambda shipping_query: True)
            async def some_pre_checkout_query_handler(shipping_query: types.ShippingQuery)

        :param state:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_pre_checkout_query_handler(callback, *custom_filters, state=state, run_task=run_task,
                                                     **kwargs)
            return callback

        return decorator

    def register_poll_handler(self, callback, *custom_filters, run_task=None, **kwargs):
        """
        Register handler for poll
        
        Example:

        .. code-block:: python3

            dp.register_poll_handler(some_poll_handler)

        :param callback:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        filters_set = self.filters_factory.resolve(self.poll_handlers,
                                                   *custom_filters,
                                                   **kwargs)
        self.poll_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def poll_handler(self, *custom_filters, run_task=None, **kwargs):
        """
        Decorator for poll handler

        Example:

        .. code-block:: python3

            @dp.poll_handler()
            async def some_poll_handler(poll: types.Poll)

        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        
        def decorator(callback):
            self.register_poll_handler(callback, *custom_filters, run_task=run_task,
                                       **kwargs)
            return callback

        return decorator
    
    def register_poll_answer_handler(self, callback, *custom_filters, run_task=None, **kwargs):
        """
        Register handler for poll_answer
        
        Example:

        .. code-block:: python3

            dp.register_poll_answer_handler(some_poll_answer_handler)

        :param callback:
        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """
        filters_set = self.filters_factory.resolve(self.poll_answer_handlers,
                                                   *custom_filters,
                                                   **kwargs)
        self.poll_answer_handlers.register(self._wrap_async_task(callback, run_task), filters_set)
    
    def poll_answer_handler(self, *custom_filters, run_task=None, **kwargs):
        """
        Decorator for poll_answer handler

        Example:

        .. code-block:: python3

            @dp.poll_answer_handler()
            async def some_poll_answer_handler(poll_answer: types.PollAnswer)

        :param custom_filters:
        :param run_task: run callback in task (no wait results)
        :param kwargs:
        """

        def decorator(callback):
            self.register_poll_answer_handler(callback, *custom_filters, run_task=run_task,
                                       **kwargs)
            return callback

        return decorator

    def register_errors_handler(self, callback, *custom_filters, exception=None, run_task=None, **kwargs):
        """
        Register handler for errors

        :param callback:
        :param exception: you can make handler for specific errors type
        :param run_task: run callback in task (no wait results)
        """
        filters_set = self.filters_factory.resolve(self.errors_handlers,
                                                   *custom_filters,
                                                   exception=exception,
                                                   **kwargs)
        self.errors_handlers.register(self._wrap_async_task(callback, run_task), filters_set)

    def errors_handler(self, *custom_filters, exception=None, run_task=None, **kwargs):
        """
        Decorator for errors handler

        :param exception: you can make handler for specific errors type
        :param run_task: run callback in task (no wait results)
        :return:
        """

        def decorator(callback):
            self.register_errors_handler(self._wrap_async_task(callback, run_task),
                                         *custom_filters, exception=exception, **kwargs)
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
            chat_obj = types.Chat.get_current()
            chat = chat_obj.id if chat_obj else None
        if user is None:
            user_obj = types.User.get_current()
            user = user_obj.id if user_obj else None

        return FSMContext(storage=self.storage, chat=chat, user=user)

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def throttle(self, key, *, rate=None, user_id=None, chat_id=None, no_error=None) -> bool:
        """
        Execute throttling manager.
        Returns True if limit has not exceeded otherwise raises ThrottleError or returns False

        :param key: key in storage
        :param rate: limit (by default is equal to default rate limit)
        :param user_id: user id
        :param chat_id: chat id
        :param no_error: return boolean value instead of raising error
        :return: bool
        """
        if not self.storage.has_bucket():
            raise RuntimeError('This storage does not provide Leaky Bucket')

        if no_error is None:
            no_error = self.no_throttle_error
        if rate is None:
            rate = self.throttling_rate_limit
        if user_id is None and chat_id is None:
            user_id = types.User.get_current().id
            chat_id = types.Chat.get_current().id

        # Detect current time
        now = time.time()

        bucket = await self.storage.get_bucket(chat=chat_id, user=user_id)

        # Fix bucket
        if bucket is None:
            bucket = {key: {}}
        if key not in bucket:
            bucket[key] = {}
        data = bucket[key]

        # Calculate
        called = data.get(LAST_CALL, now)
        delta = now - called
        result = delta >= rate or delta <= 0

        # Save results
        data[RESULT] = result
        data[RATE_LIMIT] = rate
        data[LAST_CALL] = now
        data[DELTA] = delta
        if not result:
            data[EXCEEDED_COUNT] += 1
        else:
            data[EXCEEDED_COUNT] = 1
        bucket[key].update(data)
        await self.storage.set_bucket(chat=chat_id, user=user_id, bucket=bucket)

        if not result and not no_error:
            # Raise if it is allowed
            raise Throttled(key=key, chat=chat_id, user=user_id, **data)
        return result

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def check_key(self, key, chat_id=None, user_id=None):
        """
        Get information about key in bucket

        :param key:
        :param chat_id:
        :param user_id:
        :return:
        """
        if not self.storage.has_bucket():
            raise RuntimeError('This storage does not provide Leaky Bucket')

        if user_id is None and chat_id is None:
            user_id = types.User.get_current()
            chat_id = types.Chat.get_current()

        bucket = await self.storage.get_bucket(chat=chat_id, user=user_id)
        data = bucket.get(key, {})
        return Throttled(key=key, chat=chat_id, user=user_id, **data)

    @renamed_argument(old_name='user', new_name='user_id', until_version='3.0', stacklevel=3)
    @renamed_argument(old_name='chat', new_name='chat_id', until_version='3.0', stacklevel=4)
    async def release_key(self, key, chat_id=None, user_id=None):
        """
        Release blocked key

        :param key:
        :param chat_id:
        :param user_id:
        :return:
        """
        if not self.storage.has_bucket():
            raise RuntimeError('This storage does not provide Leaky Bucket')

        if user_id is None and chat_id is None:
            user_id = types.User.get_current()
            chat_id = types.Chat.get_current()

        bucket = await self.storage.get_bucket(chat=chat_id, user=user_id)
        if bucket and key in bucket:
            del bucket['key']
            await self.storage.set_bucket(chat=chat_id, user=user_id, bucket=bucket)
            return True
        return False

    def async_task(self, func):
        """
        Execute handler as task and return None.
        Use this decorator for slow handlers (with timeouts)

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
            try:
                response = task.result()
            except Exception as e:
                self._loop_create_task(
                    self.errors_handlers.notify(types.Update.get_current(), e))
            else:
                if isinstance(response, BaseResponse):
                    self._loop_create_task(response.execute_response(self.bot))

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            task = self._loop_create_task(func(*args, **kwargs))
            task.add_done_callback(process_response)

        return wrapper

    def _wrap_async_task(self, callback, run_task=None) -> callable:
        if run_task is None:
            run_task = self.run_tasks_by_default

        if run_task:
            return self.async_task(callback)
        return callback

    def throttled(self, on_throttled: typing.Optional[typing.Callable] = None,
                  key=None, rate=None,
                  user_id=None, chat_id=None):
        """
        Meta-decorator for throttling.
        Invokes on_throttled if the handler was throttled.

        Example:

        .. code-block:: python3

            async def handler_throttled(message: types.Message, **kwargs):
                await message.answer("Throttled!")

            @dp.throttled(handler_throttled)
            async def some_handler(message: types.Message):
                await message.answer("Didn't throttled!")

        :param on_throttled: the callable object that should be either a function or return a coroutine
        :param key: key in storage
        :param rate: limit (by default is equal to default rate limit)
        :param user_id: user id
        :param chat_id: chat id
        :return: decorator
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapped(*args, **kwargs):
                is_not_throttled = await self.throttle(key if key is not None else func.__name__,
                                                       rate=rate,
                                                       user_id=user_id, chat_id=chat_id,
                                                       no_error=True)
                if is_not_throttled:
                    return await func(*args, **kwargs)
                else:
                    kwargs.update(
                        {
                            'rate': rate,
                            'key': key,
                            'user_id': user_id,
                            'chat_id': chat_id
                        }
                    )  # update kwargs with parameters which were given to throttled

                    if on_throttled:
                        if asyncio.iscoroutinefunction(on_throttled):
                            await on_throttled(*args, **kwargs)
                        else:
                            kwargs.update(
                                {
                                    'loop': asyncio.get_running_loop()
                                }
                            )
                            partial_func = functools.partial(on_throttled, *args, **kwargs)
                            asyncio.get_running_loop().run_in_executor(None,
                                                                       partial_func
                                                                       )
            return wrapped

        return decorator

    def bind_filter(self, callback: typing.Union[typing.Callable, AbstractFilter],
                    validator: typing.Optional[typing.Callable] = None,
                    event_handlers: typing.Optional[typing.List[Handler]] = None,
                    exclude_event_handlers: typing.Optional[typing.Iterable[Handler]] = None):
        """
        Register filter

        :param callback: callable or subclass of :obj:`AbstractFilter`
        :param validator: custom validator.
        :param event_handlers: list of instances of :obj:`Handler`
        :param exclude_event_handlers: list of excluded event handlers (:obj:`Handler`)
        """
        self.filters_factory.bind(callback=callback, validator=validator, event_handlers=event_handlers,
                                  exclude_event_handlers=exclude_event_handlers)

    def unbind_filter(self, callback: typing.Union[typing.Callable, AbstractFilter]):
        """
        Unregister filter

        :param callback: callable of subclass of :obj:`AbstractFilter`
        """
        self.filters_factory.unbind(callback=callback)

    def setup_middleware(self, middleware):
        """
        Setup middleware

        :param middleware:
        :return:
        """
        self.middleware.setup(middleware)
