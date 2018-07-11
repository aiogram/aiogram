import inspect
import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from aiogram import types
from aiogram.dispatcher.filters.filters import BaseFilter, Filter
from aiogram.types import CallbackQuery, ContentType, Message


class Command(Filter):
    def __init__(self, commands, prefixes='/', ignore_case=True, ignore_mention=False):
        if isinstance(commands, str):
            commands = (commands,)

        self.commands = list(map(str.lower, commands)) if ignore_case else commands
        self.prefixes = prefixes
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention

    @staticmethod
    async def check_command(message: types.Message, commands, prefixes, ignore_case=True, ignore_mention=False):
        full_command = message.text.split()[0]
        prefix, (command, _, mention) = full_command[0], full_command[1:].partition('@')

        if not ignore_mention and mention and (await message.bot.me).username.lower() != mention.lower():
            return False
        elif prefix not in prefixes:
            return False
        elif (command.lower() if ignore_case else command) not in commands:
            return False

        return {'command': Command.CommandObj(command=command, prefix=prefix, mention=mention)}

    async def check(self, message: types.Message):
        return await self.check_command(message, self.commands, self.prefixes, self.ignore_case, self.ignore_mention)

    @dataclass
    class CommandObj:
        prefix: str = '/'
        command: str = ''
        mention: str = None
        args: str = None

        @property
        def mentioned(self) -> bool:
            return bool(self.mention)

        @property
        def text(self) -> str:
            line = self.prefix + self.command
            if self.mentioned:
                line += '@' + self.mention
            if self.args:
                line += ' ' + self.args
            return line


class CommandsFilter(BaseFilter):
    """
    Check commands in message
    """
    key = 'commands'

    def __init__(self, dispatcher, commands):
        super().__init__(dispatcher)
        if isinstance(commands, str):
            commands = (commands,)
        self.commands = commands

    async def check(self, message):
        return await Command.check_command(message, self.commands, '/')


class Text(Filter):
    def __init__(self,
                 equals: Optional[str] = None,
                 contains: Optional[str] = None,
                 startswith: Optional[str] = None,
                 endswith: Optional[str] = None,
                 ignore_case=False):
        # Only one mode can be used. check it.
        check = sum(map(bool, (equals, contains, startswith, endswith)))
        if check > 1:
            args = "' and '".join([arg[0] for arg in [('equals', equals),
                                                      ('contains', contains),
                                                      ('startswith', startswith),
                                                      ('endswith', endswith)
                                                      ] if arg[1]])
            raise ValueError(f"Arguments '{args}' cannot be used together.")
        elif check == 0:
            raise ValueError(f"No one mode is specified!")

        self.equals = equals
        self.contains = contains
        self.endswith = endswith
        self.startswith = startswith
        self.ignore_case = ignore_case

    async def check(self, message: types.Message):
        text = message.text.lower() if self.ignore_case else message.text

        if self.equals:
            return text == self.equals
        elif self.contains:
            return self.contains in text
        elif self.startswith:
            return text.startswith(self.startswith)
        elif self.endswith:
            return text.endswith(self.endswith)

        return False


class RegexpFilter(BaseFilter):
    """
    Regexp filter for messages and callback query
    """
    key = 'regexp'

    def __init__(self, dispatcher, regexp):
        super().__init__(dispatcher)
        self.regexp = re.compile(regexp, flags=re.IGNORECASE | re.MULTILINE)

    async def check(self, obj):
        if isinstance(obj, Message):
            if obj.text:
                match = self.regexp.search(obj.text)
            elif obj.caption:
                match = self.regexp.search(obj.caption)
            else:
                return False
        elif isinstance(obj, CallbackQuery) and obj.data:
            match = self.regexp.search(obj.data)
        else:
            return False

        if match:
            return {'regexp': match}
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
                return {'regexp_command': search}
        return False


class ContentTypeFilter(BaseFilter):
    """
    Check message content type
    """

    key = 'content_types'
    required = True
    default = types.ContentType.TEXT

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
    required = True

    ctx_state = ContextVar('user_state')

    def __init__(self, dispatcher, state):
        from aiogram.dispatcher.filters.state import State, StatesGroup

        super().__init__(dispatcher)
        states = []
        if not isinstance(state, (list, set, tuple, frozenset)) or state is None:
            state = [state, ]
        for item in state:
            if isinstance(item, State):
                states.append(item.state)
            elif inspect.isclass(item) and issubclass(item, StatesGroup):
                states.extend(item.all_states_names)
            else:
                states.append(item)
        self.states = states

    def get_target(self, obj):
        return getattr(getattr(obj, 'chat', None), 'id', None), getattr(getattr(obj, 'from_user', None), 'id', None)

    async def check(self, obj):
        if '*' in self.states:
            return {'state': self.dispatcher.current_state()}

        try:
            state = self.ctx_state.get()
        except LookupError:
            chat, user = self.get_target(obj)

            if chat or user:
                state = await self.dispatcher.storage.get_state(chat=chat, user=user)
                self.ctx_state.set(state)
                if state in self.states:
                    return {'state': self.dispatcher.current_state(), 'raw_state': state}

        else:
            if state in self.states:
                return {'state': self.dispatcher.current_state(), 'raw_state': state}

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
