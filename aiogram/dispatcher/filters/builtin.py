import inspect
import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Union

from aiogram import types
from aiogram.dispatcher.filters.filters import BoundFilter, Filter
from aiogram.types import CallbackQuery, Message


class Command(Filter):
    """
    You can handle commands by using this filter
    """

    def __init__(self, commands: Union[Iterable, str],
                 prefixes: Union[Iterable, str] = '/',
                 ignore_case: bool = True,
                 ignore_mention: bool = False):
        """
        Filter can be initialized from filters factory or by simply creating instance of this class

        :param commands: command or list of commands
        :param prefixes:
        :param ignore_case:
        :param ignore_mention:
        """
        if isinstance(commands, str):
            commands = (commands,)

        self.commands = list(map(str.lower, commands)) if ignore_case else commands
        self.prefixes = prefixes
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention

    @classmethod
    def validate(cls, full_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validator for filters factory

        :param full_config:
        :return: config or empty dict
        """
        config = {}
        if 'commands' in full_config:
            config['commands'] = full_config.pop('commands')
        if 'commands_prefix' in full_config:
            config['prefixes'] = full_config.pop('commands_prefix')
        if 'commands_ignore_mention' in full_config:
            config['ignore_mention'] = full_config.pop('commands_ignore_mention')
        return config

    async def check(self, message: types.Message):
        return await self.check_command(message, self.commands, self.prefixes, self.ignore_case, self.ignore_mention)

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

    @dataclass
    class CommandObj:
        prefix: str = '/'
        command: str = ''
        mention: str = None
        args: str = field(repr=False, default=None)

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


class CommandStart(Command):
    def __init__(self):
        super(CommandStart, self).__init__(['start'])


class CommandHelp(Command):
    def __init__(self):
        super(CommandHelp, self).__init__(['help'])


class CommandSettings(Command):
    def __init__(self):
        super(CommandSettings, self).__init__(['settings'])


class CommandPrivacy(Command):
    def __init__(self):
        super(CommandPrivacy, self).__init__(['privacy'])


class Text(Filter):
    """
    Simple text filter
    """

    def __init__(self,
                 equals: Optional[str] = None,
                 contains: Optional[str] = None,
                 startswith: Optional[str] = None,
                 endswith: Optional[str] = None,
                 ignore_case=False):
        """
        Check text for one of pattern. Only one mode can be used in one filter.

        :param equals:
        :param contains:
        :param startswith:
        :param endswith:
        :param ignore_case: case insensitive
        """
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

    @classmethod
    def validate(cls, full_config: Dict[str, Any]):
        if 'text' in full_config:
            return {'equals': full_config.pop('text')}
        elif 'text_contains' in full_config:
            return {'contains': full_config.pop('text_contains')}
        elif 'text_startswith' in full_config:
            return {'startswith': full_config.pop('text_startswith')}
        elif 'text_endswith' in full_config:
            return {'endswith': full_config.pop('text_endswith')}

    async def check(self, obj: Union[Message, CallbackQuery]):
        if isinstance(obj, Message):
            text = obj.text or obj.caption or ''
        elif isinstance(obj, CallbackQuery):
            text = obj.data
        else:
            return False

        if self.ignore_case:
            text = text.lower()

        if self.equals:
            return text == self.equals
        elif self.contains:
            return self.contains in text
        elif self.startswith:
            return text.startswith(self.startswith)
        elif self.endswith:
            return text.endswith(self.endswith)

        return False


class HashTag(Filter):
    """
    Filter for hashtag's and cashtag's
    """

    # TODO: allow to use regexp

    def __init__(self, hashtags=None, cashtags=None):
        if not hashtags and not cashtags:
            raise ValueError('No one hashtag or cashtag is specified!')

        if hashtags is None:
            hashtags = []
        elif isinstance(hashtags, str):
            hashtags = [hashtags]

        if cashtags is None:
            cashtags = []
        elif isinstance(cashtags, str):
            cashtags = [cashtags.upper()]
        else:
            cashtags = list(map(str.upper, cashtags))

        self.hashtags = hashtags
        self.cashtags = cashtags

    @classmethod
    def validate(cls, full_config: Dict[str, Any]):
        config = {}
        if 'hashtags' in full_config:
            config['hashtags'] = full_config.pop('hashtags')
        if 'cashtags' in full_config:
            config['cashtags'] = full_config.pop('cashtags')
        return config

    async def check(self, message: types.Message):
        if message.caption:
            text = message.caption
            entities = message.caption_entities
        elif message.text:
            text = message.text
            entities = message.entities
        else:
            return False

        hashtags, cashtags = self._get_tags(text, entities)
        if self.hashtags and set(hashtags) & set(self.hashtags) \
                or self.cashtags and set(cashtags) & set(self.cashtags):
            return {'hashtags': hashtags, 'cashtags': cashtags}

    def _get_tags(self, text, entities):
        hashtags = []
        cashtags = []

        for entity in entities:
            if entity.type == types.MessageEntityType.HASHTAG:
                value = entity.get_text(text).lstrip('#')
                hashtags.append(value)

            elif entity.type == types.MessageEntityType.CASHTAG:
                value = entity.get_text(text).lstrip('$')
                cashtags.append(value)

        return hashtags, cashtags


class Regexp(Filter):
    """
    Regexp filter for messages and callback query
    """

    def __init__(self, regexp):
        if not isinstance(regexp, re.Pattern):
            regexp = re.compile(regexp, flags=re.IGNORECASE | re.MULTILINE)
        self.regexp = regexp

    @classmethod
    def validate(cls, full_config: Dict[str, Any]):
        if 'regexp' in full_config:
            return {'regexp': full_config.pop('regexp')}

    async def check(self, obj: Union[Message, CallbackQuery]):
        if isinstance(obj, Message):
            match = self.regexp.search(obj.text or obj.caption or '')
        elif isinstance(obj, CallbackQuery) and obj.data:
            match = self.regexp.search(obj.data)
        else:
            return False

        if match:
            return {'regexp': match}
        return False


class RegexpCommandsFilter(BoundFilter):
    """
    Check commands by regexp in message
    """

    key = 'regexp_commands'

    def __init__(self, regexp_commands):
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


class ContentTypeFilter(BoundFilter):
    """
    Check message content type
    """

    key = 'content_types'
    required = True
    default = types.ContentTypes.TEXT

    def __init__(self, content_types):
        self.content_types = content_types

    async def check(self, message):
        return types.ContentType.ANY in self.content_types or \
               message.content_type in self.content_types


class StateFilter(BoundFilter):
    """
    Check user state
    """
    key = 'state'
    required = True

    ctx_state = ContextVar('user_state')

    def __init__(self, dispatcher, state):
        from aiogram.dispatcher.filters.state import State, StatesGroup

        self.dispatcher = dispatcher
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


class ExceptionsFilter(BoundFilter):
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
