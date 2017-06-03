import inspect
import re


async def check_filter(filter_, args, kwargs):
    if any((inspect.isasyncgen(filter_),
            inspect.iscoroutine(filter_),
            inspect.isawaitable(filter_),
            inspect.isasyncgenfunction(filter_),
            inspect.iscoroutinefunction(filter_))):
        return await filter_(*args, **kwargs)
    elif callable(filter_):
        return filter_(*args, **kwargs)
    else:
        return True


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
        self.regexp = re.compile(regexp)

    def check(self, message):
        if message.text:
            return bool(self.regexp.match(message.text))


class ContentTypeFilter(Filter):
    def __init__(self, content_types):
        self.content_types = content_types

    def check(self, message):
        return message.content_type in self.content_types


class CancelFilter(Filter):
    def __init__(self, cancel_set=None):
        if cancel_set is None:
            cancel_set = ['/cancel', 'cancel', 'cancel.']
        self.cancel_set = cancel_set

    def check(self, message):
        if message.text:
            return message.text.lower() in self.cancel_set


def generate_default_filters(*args, **kwargs):
    filters_set = []

    for name, filter_ in kwargs.items():
        if filter_ is None:
            continue
        if name == 'commands':
            if isinstance(filter_, str):
                filters_set.append(CommandsFilter([filter_]))
            else:
                filters_set.append(CommandsFilter(filter_))
        elif name == 'regexp':
            filters_set.append(RegexpFilter(filter_))
        elif name == 'content_types':
            filters_set.append(ContentTypeFilter(filter_))
        elif name == 'func':
            filters_set.append(filter_)

    filters_set += list(args)

    return filters_set


class DefaultFilters:
    COMMANDS = 'commands'
    REGEXP = 'regexp'
    CONTENT_TYPE = 'content_type'
    FUNC = 'func'
