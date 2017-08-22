import asyncio
import functools
import logging
import typing

from .filters import CommandsFilter, RegexpFilter, ContentTypeFilter, generate_default_filters
from .handler import Handler
from .storage import DisabledStorage, BaseStorage, FSMContext
from .webhook import BaseResponse
from ..bot import Bot
from ..types.message import ContentType
from ..utils.exceptions import TelegramAPIError, NetworkError

log = logging.getLogger(__name__)


class Dispatcher:
    """
    Simple Updates dispatcher

    It will be can process incoming updates, messages, edited messages, channel posts, edited channels posts,
    inline query, chosen inline result, callback query, shipping query, pre-checkout query.
    Provide next step handler and etc.
    """

    def __init__(self, bot, loop=None, storage: typing.Optional[BaseStorage] = None):
        if loop is None:
            loop = bot.loop
        if storage is None:
            storage = DisabledStorage()

        self.bot: Bot = bot
        self.loop = loop
        self.storage = storage

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

        self._pooling = False

    def __del__(self):
        self._pooling = False

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
            tasks.append(self.updates_handler.notify(update))
        return await asyncio.gather(*tasks)

    async def process_update(self, update):
        """
        Process single update object

        :param update:
        :return:
        """
        self.last_update_id = update.update_id
        if update.message:
            return await self.message_handlers.notify(update.message)
        if update.edited_message:
            return await self.edited_message_handlers.notify(update.edited_message)
        if update.channel_post:
            return await self.channel_post_handlers.notify(update.channel_post)
        if update.edited_channel_post:
            return await self.edited_channel_post_handlers.notify(update.edited_channel_post)
        if update.inline_query:
            return await self.inline_query_handlers.notify(update.inline_query)
        if update.chosen_inline_result:
            return await self.chosen_inline_result_handlers.notify(update.chosen_inline_result)
        if update.callback_query:
            return await self.callback_query_handlers.notify(update.callback_query)
        if update.shipping_query:
            return await self.shipping_query_handlers.notify(update.shipping_query)
        if update.pre_checkout_query:
            return await self.pre_checkout_query_handlers.notify(update.pre_checkout_query)

    async def start_pooling(self, timeout=20, relax=0.1, limit=None):
        """
        Start long-pooling

        :param timeout:
        :param relax:
        :param limit:
        :return:
        """
        if self._pooling:
            raise RuntimeError('Pooling already started')
        log.info('Start pooling.')

        self._pooling = True
        offset = None
        while self._pooling:
            try:
                updates = await self.bot.get_updates(limit=limit, offset=offset, timeout=timeout)
            except NetworkError:
                log.exception('Cause exception while getting updates.')
                await asyncio.sleep(15)
                continue

            if updates:
                log.info("Received {0} updates.".format(len(updates)))
                offset = updates[-1].update_id + 1

                self.loop.create_task(self._process_pooling_updates(updates))

            if relax:
                await asyncio.sleep(relax)

        log.warning('Pooling is stopped.')

    async def _process_pooling_updates(self, updates):
        """
        Process updates received from long-pooling.

        :param updates: list of updates.
        """
        need_to_call = []
        for update in await self.process_updates(updates):
            for responses in update:
                for response in responses:
                    if not isinstance(response, BaseResponse):
                        continue
                    need_to_call.append(response.execute_response(self.bot))
        if need_to_call:
            try:
                asyncio.gather(*need_to_call)
            except TelegramAPIError:
                log.exception('Cause exception while processing updates.')

    def stop_pooling(self):
        """
        Break long-pooling process.
        :return:
        """
        self._pooling = False

    def register_message_handler(self, callback, *, commands=None, regexp=None, content_types=None, func=None,
                                 state=None, custom_filters=None, **kwargs):
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
        self.message_handlers.register(callback, filters_set)

    def message_handler(self, *, commands=None, regexp=None, content_types=None, func=None, state=None,
                        custom_filters=None, **kwargs):
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
        :return: decorated function
        """

        def decorator(callback):
            self.register_message_handler(callback,
                                          commands=commands, regexp=regexp, content_types=content_types,
                                          func=func, state=state, custom_filters=custom_filters, **kwargs)
            return callback

        return decorator

    def register_edited_message_handler(self, callback, *, commands=None, regexp=None, content_types=None, func=None,
                                        state=None, custom_filters=None, **kwargs):
        """
        Analog of message_handler but only for edited messages

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
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
        self.edited_message_handlers.register(callback, filters_set)

    def edited_message_handler(self, *, commands=None, regexp=None, content_types=None, func=None, state=None,
                               custom_filters=None, **kwargs):
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
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_edited_message_handler(callback, commands=commands, regexp=regexp,
                                                 content_types=content_types, func=func, state=state,
                                                 custom_filters=custom_filters, **kwargs)
            return callback

        return decorator

    def register_channel_post_handler(self, callback, *, commands=None, regexp=None, content_types=None, func=None,
                                      state=None, custom_filters=None, **kwargs):
        """
        Register channels posts handler

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
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
        self.channel_post_handlers.register(callback, filters_set)

    def channel_post_handler(self, *, commands=None, regexp=None, content_types=None, func=None, state=None,
                             custom_filters=None, **kwargs):
        """
        Register channels posts handler

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_channel_post_handler(commands=commands, regexp=regexp, content_types=content_types,
                                               func=func, state=state, custom_filters=custom_filters, **kwargs)
            return callback

        return decorator

    def register_edited_channel_post_handler(self, callback, *, commands=None, regexp=None, content_types=None,
                                             func=None, state=None, custom_filters=None, **kwargs):
        """
        Register handler for edited channels posts

        :param callback:
        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
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
        self.edited_channel_post_handlers.register(callback, filters_set)

    def edited_channel_post_handler(self, *, commands=None, regexp=None, content_types=None, func=None, state=None,
                                    custom_filters=None, **kwargs):
        """
        Register handler for edited channels posts

        :param commands: list of commands
        :param regexp: REGEXP
        :param content_types: List of content types.
        :param func: custom any callable object
        :param custom_filters: list of custom filters
        :param state:
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_edited_channel_post_handler(callback, commands=commands, regexp=regexp,
                                                      content_types=content_types, func=func, state=state,
                                                      custom_filters=custom_filters, **kwargs)
            return callback

        return decorator

    def register_inline_handler(self, callback, *, func=None, state=None, custom_filters=None, **kwargs):
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
        self.inline_query_handlers.register(callback, filters_set)

    def inline_handler(self, *, func=None, state=None, custom_filters=None, **kwargs):
        """
        Handle inline query

        Example:

        .. code-block:: python3

            @dp.inline_handler(func=lambda inline_query: True)
            async def handler(inline_query: types.InlineQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters: list of custom filters
        :param kwargs:
        :return: decorated function
        """

        def decorator(callback):
            self.register_inline_handler(callback, func=func, state=state, custom_filters=custom_filters, **kwargs)
            return callback

        return decorator

    def register_chosen_inline_handler(self, callback, *, func=None, state=None, custom_filters=None, **kwargs):
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
        self.chosen_inline_result_handlers.register(callback, filters_set)

    def chosen_inline_handler(self, *, func=None, state=None, custom_filters=None, **kwargs):
        """
        Register chosen inline handler

        Example:

        .. code-block:: python3

            @dp.chosen_inline_handler(func=lambda chosen_inline_query: True)
            async def handler(chosen_inline_query: types.ChosenInlineResult)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param kwargs:
        :return:
        """

        def decorator(callback):
            self.register_chosen_inline_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                **kwargs)
            return callback

        return decorator

    def register_callback_query_handler(self, callback, *, func=None, state=None, custom_filters=None, **kwargs):
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
        :param kwargs:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.chosen_inline_result_handlers.register(callback, filters_set)

    def callback_query_handler(self, *, func=None, state=None, custom_filters=None, **kwargs):
        """
        Add callback query handler

        Example:

        .. code-block:: python3

            @dp.callback_query_handler(func=lambda callback_query: True)
            async def handler(callback_query: types.CallbackQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param kwargs:
        """

        def decorator(callback):
            self.register_callback_query_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                 **kwargs)
            return callback

        return decorator

    def register_shipping_query_handler(self, callback, *, func=None, state=None, custom_filters=None, **kwargs):
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
        :param kwargs:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.shipping_query_handlers.register(callback, filters_set)

    def shipping_query_handler(self, *, func=None, state=None, custom_filters=None, **kwargs):
        """
        Add shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(func=lambda shipping_query: True)
            async def handler(shipping_query: types.ShippingQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param kwargs:
        """

        def decorator(callback):
            self.register_shipping_query_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                 **kwargs)
            return callback

        return decorator

    def register_pre_checkout_query_handler(self, callback, *, func=None, state=None, custom_filters=None, **kwargs):
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
        :param kwargs:
        """
        if custom_filters is None:
            custom_filters = []
        filters_set = generate_default_filters(self,
                                               *custom_filters,
                                               func=func,
                                               state=state,
                                               **kwargs)
        self.pre_checkout_query_handlers.register(callback, filters_set)

    def pre_checkout_query_handler(self, *, func=None, state=None, custom_filters=None, **kwargs):
        """
        Add shipping query handler

        Example:

        .. code-block:: python3

            @dp.shipping_query_handler(func=lambda shipping_query: True)
            async def handler(shipping_query: types.ShippingQuery)

        :param func: custom any callable object
        :param state:
        :param custom_filters:
        :param kwargs:
        """

        def decorator(callback):
            self.register_pre_checkout_query_handler(callback, func=func, state=state, custom_filters=custom_filters,
                                                     **kwargs)
            return callback

        return decorator

    def current_state(self, *,
                      chat: typing.Union[str, int, None] = None,
                      user: typing.Union[str, int, None] = None) -> FSMContext:
        return FSMContext(storage=self.storage, chat=chat, user=user)

    def async_task(self, func):
        def process_response(task):
            response = task.result()
            self.loop.create_task(response.execute_response(self.bot))

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            task = self.loop.create_task(func(*args, **kwargs))
            task.add_done_callback(process_response)

        return wrapper
