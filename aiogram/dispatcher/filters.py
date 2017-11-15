import asyncio
import inspect
import re

from ..types import ContentType
from ..utils import context
from ..utils.helper import Helper, HelperMode, Item

USER_STATE = 'USER_STATE'


async def check_filter(filter_, args, kwargs):
    if not callable(filter_):
        raise TypeError('Filter must be callable and/or awaitable!')

    if inspect.isawaitable(filter_) or inspect.iscoroutinefunction(filter_):
        return await filter_(*args, **kwargs)
    else:
        return filter_(*args, **kwargs)


async def check_filters(filters, args, kwargs):
    if filters is not None:
        for filter_ in filters:
            f = await check_filter(filter_, args, kwargs)
            if not f:
                return False
    return True


class Filter:
    def __call__(self, *args, **kwargs):
        return self.check(*args, **kwargs)

    def check(self, *args, **kwargs):
        raise NotImplementedError


class AsyncFilter(Filter):
    def __aiter__(self):
        return None

    def __await__(self):
        return self.check

    async def check(self, *args, **kwargs):
        pass


class AnyFilter(AsyncFilter):
    def __init__(self, *filters: callable):
        self.filters = filters

    async def check(self, *args, **kwargs):
        f = (check_filter(filter_, args, kwargs) for filter_ in self.filters)
        return any(await asyncio.gather(*f))


class NotFilter(AsyncFilter):
    def __init__(self, filter_: callable):
        self.filter = filter_

    async def check(self, *args, **kwargs):
        return not await check_filter(self.filter, args, kwargs)


class CommandsFilter(AsyncFilter):
    def __init__(self, commands):
        self.commands = commands

    async def check(self, message):
        if not message.is_command():
            return False

        command = message.text.split()[0][1:]
        command, _, mention = command.partition('@')

        if mention and mention != (await message.bot.me).username:
            return False

        if command not in self.commands:
            return False

        return True


class RegexpFilter(Filter):
    def __init__(self, regexp):
        self.regexp = re.compile(regexp, flags=re.IGNORECASE | re.MULTILINE)

    def check(self, message):
        if message.text:
            return bool(self.regexp.search(message.text))


class ContentTypeFilter(Filter):
    def __init__(self, content_types):
        self.content_types = content_types

    def check(self, message):
        return ContentType.ANY[0] in self.content_types or \
               message.content_type in self.content_types


class CancelFilter(Filter):
    def __init__(self, cancel_set=None):
        if cancel_set is None:
            cancel_set = ['/cancel', 'cancel', 'cancel.']
        self.cancel_set = cancel_set

    def check(self, message):
        if message.text:
            return message.text.lower() in self.cancel_set


class StateFilter(AsyncFilter):
    def __init__(self, dispatcher, state):
        self.dispatcher = dispatcher
        self.state = state

    def get_target(self, obj):
        return getattr(getattr(obj, 'chat', None), 'id', None), getattr(getattr(obj, 'from_user', None), 'id', None)

    async def check(self, obj):
        if self.state == '*':
            return True

        if context.check_value(USER_STATE):
            context_state = context.get_value(USER_STATE)
            return self.state == context_state
        else:
            chat, user = self.get_target(obj)

            if chat or user:
                return await self.dispatcher.storage.get_state(chat=chat, user=user) == self.state
        return False


class StatesListFilter(StateFilter):
    async def check(self, obj):
        chat, user = self.get_target(obj)

        if chat or user:
            return await self.dispatcher.storage.get_state(chat=chat, user=user) in self.state
        return False


class ExceptionsFilter(Filter):
    def __init__(self, exception):
        self.exception = exception

    def check(self, dispatcher, update, exception):
        try:
            raise exception
        except self.exception:
            return True
        except:
            return False


def generate_default_filters(dispatcher, *args, **kwargs):
    filters_set = []

    for name, filter_ in kwargs.items():
        if filter_ is None and name != DefaultFilters.STATE:
            continue
        if name == DefaultFilters.COMMANDS:
            if isinstance(filter_, str):
                filters_set.append(CommandsFilter([filter_]))
            else:
                filters_set.append(CommandsFilter(filter_))
        elif name == DefaultFilters.REGEXP:
            filters_set.append(RegexpFilter(filter_))
        elif name == DefaultFilters.CONTENT_TYPES:
            filters_set.append(ContentTypeFilter(filter_))
        elif name == DefaultFilters.FUNC:
            filters_set.append(filter_)
        elif name == DefaultFilters.STATE:
            if isinstance(filter_, (list, set, tuple)):
                filters_set.append(filters_set.append(StatesListFilter(dispatcher, filter_)))
            else:
                filters_set.append(StateFilter(dispatcher, filter_))
        elif isinstance(filter_, Filter):
            filters_set.append(filter_)

    filters_set += list(args)

    return filters_set


class DefaultFilters(Helper):
    mode = HelperMode.snake_case

    COMMANDS = Item()  # commands
    REGEXP = Item()  # regexp
    CONTENT_TYPES = Item()  # content_type
    FUNC = Item()  # func
    STATE = Item()  # state
