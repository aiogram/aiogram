import asyncio
import re
from _contextvars import ContextVar

from aiogram.dispatcher.filters.filters import BaseFilter, Filter, check_filter
from aiogram.types import CallbackQuery, ContentType, Message

USER_STATE = 'USER_STATE'


class AnyFilter(Filter):
    """
    One filter from many
    """

    def __init__(self, *filters: callable):
        self.filters = filters
        super().__init__()

    async def check(self, *args):
        f = (check_filter(filter_, args) for filter_ in self.filters)
        return any(await asyncio.gather(*f))


class NotFilter(Filter):
    """
    Reverse filter
    """

    def __init__(self, filter_: callable):
        self.filter = filter_
        super().__init__()

    async def check(self, *args):
        return not await check_filter(self.filter, args)


class CommandsFilter(BaseFilter):
    """
    Check commands in message
    """
    key = 'commands'

    def __init__(self, dispatcher, commands):
        super().__init__(dispatcher)
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


class RegexpFilter(BaseFilter):
    """
    Regexp filter for messages and callback query
    """
    key = 'regexp'

    def __init__(self, dispatcher, regexp):
        super().__init__(dispatcher)
        self.regexp = re.compile(regexp, flags=re.IGNORECASE | re.MULTILINE)

    async def check(self, obj):
        if isinstance(obj, Message) and obj.text:
            return bool(self.regexp.search(obj.text))
        elif isinstance(obj, CallbackQuery) and obj.data:
            return bool(self.regexp.search(obj.data))
        return False


class RegexpCommandsFilter(BaseFilter):
    """
    Check commands by regexp in message
    """

    key = 'regexp_commands'

    def __init__(self, dispatcher, regexp_commands):
        super().__init__(dispatcher)
        self.regexp_commands = [re.compile(command, flags=re.IGNORECASE | re.MULTILINE) for command in regexp_commands]

    async def check(self, message):
        if not message.is_command():
            return False

        command = message.text.split()[0][1:]
        command, _, mention = command.partition('@')

        if mention and mention != (await message.bot.me).username:
            return False

        for command in self.regexp_commands:
            search = command.search(message.text)
            if search:
                message.conf['regexp_command'] = search
                return True
        return False


class ContentTypeFilter(BaseFilter):
    """
    Check message content type
    """

    key = 'content_types'

    def __init__(self, dispatcher, content_types):
        super().__init__(dispatcher)
        self.content_types = content_types

    async def check(self, message):
        return ContentType.ANY[0] in self.content_types or \
               message.content_type in self.content_types


class StateFilter(BaseFilter):
    """
    Check user state
    """
    key = 'state'

    ctx_state = ContextVar('user_state')

    def __init__(self, dispatcher, state):
        super().__init__(dispatcher)
        if isinstance(state, str):
            state = (state,)
        self.state = state

    def get_target(self, obj):
        return getattr(getattr(obj, 'chat', None), 'id', None), getattr(getattr(obj, 'from_user', None), 'id', None)

    async def check(self, obj):
        if self.state == '*':
            return True

        try:
            return self.state == self.ctx_state.get()
        except LookupError:
            chat, user = self.get_target(obj)

            if chat or user:
                state = await self.dispatcher.storage.get_state(chat=chat, user=user) in self.state
                self.ctx_state.set(state)
                return state == self.state

        return False


class StatesListFilter(StateFilter):
    """
    List of states
    """

    async def check(self, obj):
        chat, user = self.get_target(obj)

        if chat or user:
            return await self.dispatcher.storage.get_state(chat=chat, user=user) in self.state
        return False


class ExceptionsFilter(BaseFilter):
    """
    Filter for exceptions
    """

    key = 'exception'

    def __init__(self, dispatcher, exception):
        super().__init__(dispatcher)
        self.exception = exception

    async def check(self, dispatcher, update, exception):
        try:
            raise exception
        except self.exception:
            return True
        except:
            return False
