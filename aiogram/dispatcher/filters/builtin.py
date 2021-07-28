import inspect
import re
import typing
import warnings
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Union

from babel.support import LazyProxy

from aiogram import types
from aiogram.dispatcher.filters.filters import BoundFilter, Filter
from aiogram.types import CallbackQuery, ChatType, InlineQuery, Message, Poll, ChatMemberUpdated

ChatIDArgumentType = typing.Union[typing.Iterable[typing.Union[int, str]], str, int]


def extract_chat_ids(chat_id: ChatIDArgumentType) -> typing.Set[int]:
    # since "str" is also an "Iterable", we have to check for it first
    if isinstance(chat_id, str):
        return {int(chat_id), }
    if isinstance(chat_id, Iterable):
        return {int(item) for (item) in chat_id}
    # the last possible type is a single "int"
    return {chat_id, }


class Command(Filter):
    """
    You can handle commands by using this filter.

    If filter is successful processed the :obj:`Command.CommandObj` will be passed to the handler arguments.

    By default this filter is registered for messages and edited messages handlers.
    """

    def __init__(self, commands: Union[Iterable, str],
                 prefixes: Union[Iterable, str] = '/',
                 ignore_case: bool = True,
                 ignore_mention: bool = False,
                 ignore_caption: bool = True):
        """
        Filter can be initialized from filters factory or by simply creating instance of this class.

        Examples:

        .. code-block:: python

            @dp.message_handler(commands=['myCommand'])
            @dp.message_handler(Command(['myCommand']))
            @dp.message_handler(commands=['myCommand'], commands_prefix='!/')

        :param commands: Command or list of commands always without leading slashes (prefix)
        :param prefixes: Allowed commands prefix. By default is slash.
            If you change the default behavior pass the list of prefixes to this argument.
        :param ignore_case: Ignore case of the command
        :param ignore_mention: Ignore mention in command
            (By default this filter pass only the commands addressed to current bot)
        :param ignore_caption: Ignore caption from message (in message types like photo, video, audio, etc)
            By default is True. If you want check commands in captions, you also should set required content_types.

            Examples:

            .. code-block:: python

                @dp.message_handler(commands=['myCommand'], commands_ignore_caption=False, content_types=ContentType.ANY)
                @dp.message_handler(Command(['myCommand'], ignore_caption=False), content_types=[ContentType.TEXT, ContentType.DOCUMENT])
        """
        if isinstance(commands, str):
            commands = (commands,)

        self.commands = list(map(str.lower, commands)) if ignore_case else commands
        self.prefixes = prefixes
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.ignore_caption = ignore_caption

    @classmethod
    def validate(cls, full_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validator for filters factory

        From filters factory this filter can be registered with arguments:

         - ``command``
         - ``commands_prefix`` (will be passed as ``prefixes``)
         - ``commands_ignore_mention`` (will be passed as ``ignore_mention``)
         - ``commands_ignore_caption`` (will be passed as ``ignore_caption``)

        :param full_config:
        :return: config or empty dict
        """
        config = {}
        if 'commands' in full_config:
            config['commands'] = full_config.pop('commands')
        if config and 'commands_prefix' in full_config:
            config['prefixes'] = full_config.pop('commands_prefix')
        if config and 'commands_ignore_mention' in full_config:
            config['ignore_mention'] = full_config.pop('commands_ignore_mention')
        if config and 'commands_ignore_caption' in full_config:
            config['ignore_caption'] = full_config.pop('commands_ignore_caption')
        return config

    async def check(self, message: types.Message):
        return await self.check_command(message, self.commands, self.prefixes, self.ignore_case, self.ignore_mention, self.ignore_caption)

    @classmethod
    async def check_command(cls, message: types.Message, commands, prefixes, ignore_case=True, ignore_mention=False, ignore_caption=True):
        text = message.text or (message.caption if not ignore_caption else None)
        if not text:
            return False

        full_command, *args_list = text.split(maxsplit=1)
        args = args_list[0] if args_list else None
        prefix, (command, _, mention) = full_command[0], full_command[1:].partition('@')

        if not ignore_mention and mention and (await message.bot.me).username.lower() != mention.lower():
            return False
        if prefix not in prefixes:
            return False
        if (command.lower() if ignore_case else command) not in commands:
            return False

        return {'command': cls.CommandObj(command=command, prefix=prefix, mention=mention, args=args)}

    @dataclass
    class CommandObj:
        """
        Instance of this object is always has command and it prefix.

        Can be passed as keyword argument ``command`` to the handler
        """

        """Command prefix"""
        prefix: str = '/'
        """Command without prefix and mention"""
        command: str = ''
        """Mention (if available)"""
        mention: str = None
        """Command argument"""
        args: str = field(repr=False, default=None)

        @property
        def mentioned(self) -> bool:
            """
            This command has mention?

            :return:
            """
            return bool(self.mention)

        @property
        def text(self) -> str:
            """
            Generate original text from object

            :return:
            """
            line = self.prefix + self.command
            if self.mentioned:
                line += '@' + self.mention
            if self.args:
                line += ' ' + self.args
            return line


class CommandStart(Command):
    """
    This filter based on :obj:`Command` filter but can handle only ``/start`` command.
    """

    def __init__(self,
                 deep_link: typing.Optional[typing.Union[str, typing.Pattern[str]]] = None,
                 encoded: bool = False):
        """
        Also this filter can handle `deep-linking <https://core.telegram.org/bots#deep-linking>`_ arguments.

        Example:

        .. code-block:: python

            @dp.message_handler(CommandStart(re.compile(r'ref-([\\d]+)')))

        :param deep_link: string or compiled regular expression (by ``re.compile(...)``).
        :param encoded: set True if you're waiting for encoded payload (default - False).
        """
        super().__init__(['start'])
        self.deep_link = deep_link
        self.encoded = encoded

    async def check(self, message: types.Message):
        """
        If deep-linking is passed to the filter result of the matching will be passed as ``deep_link`` to the handler

        :param message:
        :return:
        """
        from ...utils.deep_linking import decode_payload
        check = await super().check(message)

        if check and self.deep_link is not None:
            payload = decode_payload(message.get_args()) if self.encoded else message.get_args()

            if not isinstance(self.deep_link, typing.Pattern):
                return False if payload != self.deep_link else {'deep_link': payload}

            match = self.deep_link.match(payload)
            if match:
                return {'deep_link': match}
            return False

        return check


class CommandHelp(Command):
    """
    This filter based on :obj:`Command` filter but can handle only ``/help`` command.
    """

    def __init__(self):
        super().__init__(['help'])


class CommandSettings(Command):
    """
    This filter based on :obj:`Command` filter but can handle only ``/settings`` command.
    """

    def __init__(self):
        super().__init__(['settings'])


class CommandPrivacy(Command):
    """
    This filter based on :obj:`Command` filter but can handle only ``/privacy`` command.
    """

    def __init__(self):
        super().__init__(['privacy'])


class Text(Filter):
    """
    Simple text filter
    """

    _default_params = (
        ('text', 'equals'),
        ('text_contains', 'contains'),
        ('text_startswith', 'startswith'),
        ('text_endswith', 'endswith'),
    )

    def __init__(self,
                 equals: Optional[Union[str, LazyProxy, Iterable[Union[str, LazyProxy]]]] = None,
                 contains: Optional[Union[str, LazyProxy, Iterable[Union[str, LazyProxy]]]] = None,
                 startswith: Optional[Union[str, LazyProxy, Iterable[Union[str, LazyProxy]]]] = None,
                 endswith: Optional[Union[str, LazyProxy, Iterable[Union[str, LazyProxy]]]] = None,
                 ignore_case=False):
        """
        Check text for one of pattern. Only one mode can be used in one filter.
        In every pattern, a single string is treated as a list with 1 element.

        :param equals: True if object's text in the list
        :param contains: True if object's text contains all strings from the list
        :param startswith: True if object's text starts with any of strings from the list
        :param endswith: True if object's text ends with any of strings from the list
        :param ignore_case: case insensitive
        """
        # Only one mode can be used. check it.
        check = sum(map(lambda s: s is not None, (equals, contains, startswith, endswith)))
        if check > 1:
            args = "' and '".join([arg[0] for arg in [('equals', equals),
                                                      ('contains', contains),
                                                      ('startswith', startswith),
                                                      ('endswith', endswith)
                                                      ] if arg[1] is not None])
            raise ValueError(f"Arguments '{args}' cannot be used together.")
        elif check == 0:
            raise ValueError(f"No one mode is specified!")

        equals, contains, endswith, startswith = map(
            lambda e: [e] if isinstance(e, (str, LazyProxy)) else e,
            (equals, contains, endswith, startswith),
        )
        self.equals = equals
        self.contains = contains
        self.endswith = endswith
        self.startswith = startswith
        self.ignore_case = ignore_case

    @classmethod
    def validate(cls, full_config: Dict[str, Any]):
        for param, key in cls._default_params:
            if param in full_config:
                return {key: full_config.pop(param)}

    async def check(self, obj: Union[Message, CallbackQuery, InlineQuery, Poll]):
        if isinstance(obj, Message):
            text = obj.text or obj.caption or ''
            if not text and obj.poll:
                text = obj.poll.question
        elif isinstance(obj, CallbackQuery):
            text = obj.data
        elif isinstance(obj, InlineQuery):
            text = obj.query
        elif isinstance(obj, Poll):
            text = obj.question
        else:
            return False

        if self.ignore_case:
            text = text.lower()
            _pre_process_func = lambda s: str(s).lower()
        else:
            _pre_process_func = str

        # now check
        if self.equals is not None:
            equals = list(map(_pre_process_func, self.equals))
            return text in equals

        if self.contains is not None:
            contains = list(map(_pre_process_func, self.contains))
            return all(map(text.__contains__, contains))

        if self.startswith is not None:
            startswith = list(map(_pre_process_func, self.startswith))
            return any(map(text.startswith, startswith))

        if self.endswith is not None:
            endswith = list(map(_pre_process_func, self.endswith))
            return any(map(text.endswith, endswith))

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
        if not isinstance(regexp, typing.Pattern):
            regexp = re.compile(regexp, flags=re.IGNORECASE | re.MULTILINE)
        self.regexp = regexp

    @classmethod
    def validate(cls, full_config: Dict[str, Any]):
        if 'regexp' in full_config:
            return {'regexp': full_config.pop('regexp')}

    async def check(self, obj: Union[Message, CallbackQuery, InlineQuery, Poll]):
        if isinstance(obj, Message):
            content = obj.text or obj.caption or ''
            if not content and obj.poll:
                content = obj.poll.question
        elif isinstance(obj, CallbackQuery) and obj.data:
            content = obj.data
        elif isinstance(obj, InlineQuery):
            content = obj.query
        elif isinstance(obj, Poll):
            content = obj.question
        else:
            return False

        match = self.regexp.search(content)

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
        if isinstance(content_types, str):
            content_types = (content_types,)
        self.content_types = content_types

    async def check(self, message):
        return types.ContentType.ANY in self.content_types or \
               message.content_type in self.content_types


class IsSenderContact(BoundFilter):
    """
    Filter check that the contact matches the sender

    `is_sender_contact=True` - contact matches the sender
    `is_sender_contact=False` - result will be inverted
    """
    key = 'is_sender_contact'

    def __init__(self, is_sender_contact: bool):
        self.is_sender_contact = is_sender_contact

    async def check(self, message: types.Message) -> bool:
        if not message.contact:
            return False
        is_sender_contact = message.contact.user_id == message.from_user.id
        if self.is_sender_contact:
            return is_sender_contact
        else:
            return not is_sender_contact


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
        if isinstance(obj, CallbackQuery):
            return getattr(getattr(getattr(obj, 'message', None),'chat', None), 'id', None), getattr(getattr(obj, 'from_user', None), 'id', None)
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

    def __init__(self, exception):
        self.exception = exception

    async def check(self, update, exception):
        try:
            raise exception
        except self.exception:
            return True
        except:
            return False


class IDFilter(Filter):
    def __init__(self,
                 user_id: Optional[ChatIDArgumentType] = None,
                 chat_id: Optional[ChatIDArgumentType] = None,
                 ):
        """
        :param user_id:
        :param chat_id:
        """
        if user_id is None and chat_id is None:
            raise ValueError("Both user_id and chat_id can't be None")

        self.user_id: Optional[typing.Set[int]] = None
        self.chat_id: Optional[typing.Set[int]] = None

        if user_id:
            self.user_id = extract_chat_ids(user_id)

        if chat_id:
            self.chat_id = extract_chat_ids(chat_id)

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        result = {}
        if 'user_id' in full_config:
            result['user_id'] = full_config.pop('user_id')

        if 'chat_id' in full_config:
            result['chat_id'] = full_config.pop('chat_id')

        return result

    async def check(self, obj: Union[Message, CallbackQuery, InlineQuery, ChatMemberUpdated]):
        if isinstance(obj, Message):
            user_id = None
            if obj.from_user is not None:
                user_id = obj.from_user.id
            chat_id = obj.chat.id
        elif isinstance(obj, CallbackQuery):
            user_id = obj.from_user.id
            chat_id = None
            if obj.message is not None:
                # if the button was sent with message
                chat_id = obj.message.chat.id
        elif isinstance(obj, InlineQuery):
            user_id = obj.from_user.id
            chat_id = None
        elif isinstance(obj, ChatMemberUpdated):
            user_id = obj.from_user.id
            chat_id = obj.chat.id
        else:
            return False

        if self.user_id and self.chat_id:
            return user_id in self.user_id and chat_id in self.chat_id
        if self.user_id:
            return user_id in self.user_id
        if self.chat_id:
            return chat_id in self.chat_id

        return False


class AdminFilter(Filter):
    """
    Checks if user is admin in a chat.
    If is_chat_admin is not set, the filter will check in the current chat (correct only for messages).
    is_chat_admin is required for InlineQuery.
    """

    def __init__(self, is_chat_admin: Optional[Union[ChatIDArgumentType, bool]] = None):
        self._check_current = False
        self._chat_ids = None

        if is_chat_admin is False:
            raise ValueError("is_chat_admin cannot be False")

        if not is_chat_admin:
            self._check_current = True
            return

        if isinstance(is_chat_admin, bool):
            self._check_current = is_chat_admin
        self._chat_ids = extract_chat_ids(is_chat_admin)

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]) -> typing.Optional[typing.Dict[str, typing.Any]]:
        result = {}

        if "is_chat_admin" in full_config:
            result["is_chat_admin"] = full_config.pop("is_chat_admin")

        return result

    async def check(self, obj: Union[Message, CallbackQuery, InlineQuery, ChatMemberUpdated]) -> bool:
        user_id = obj.from_user.id

        if self._check_current:
            if isinstance(obj, Message):
                chat = obj.chat
            elif isinstance(obj, CallbackQuery) and obj.message:
                chat = obj.message.chat
            elif isinstance(obj, ChatMemberUpdated):
                chat = obj.chat
            else:
                return False
            if chat.type == ChatType.PRIVATE:  # there is no admin in private chats
                return False
            chat_ids = [chat.id]
        else:
            chat_ids = self._chat_ids

        admins = [member.user.id for chat_id in chat_ids for member in await obj.bot.get_chat_administrators(chat_id)]

        return user_id in admins


class IsReplyFilter(BoundFilter):
    """
    Check if message is replied and send reply message to handler
    """
    key = 'is_reply'

    def __init__(self, is_reply):
        self.is_reply = is_reply

    async def check(self, msg: Message):
        if msg.reply_to_message and self.is_reply:
            return {'reply': msg.reply_to_message}
        elif not msg.reply_to_message and not self.is_reply:
            return True


class ForwardedMessageFilter(BoundFilter):
    key = 'is_forwarded'

    def __init__(self, is_forwarded: bool):
        self.is_forwarded = is_forwarded

    async def check(self, message: Message):
        return bool(getattr(message, "forward_date")) is self.is_forwarded


class ChatTypeFilter(BoundFilter):
    key = 'chat_type'

    def __init__(self, chat_type: typing.Container[ChatType]):
        if isinstance(chat_type, str):
            chat_type = {chat_type}

        self.chat_type: typing.Set[str] = set(chat_type)

    async def check(self, obj: Union[Message, CallbackQuery, ChatMemberUpdated]):
        if isinstance(obj, Message):
            obj = obj.chat
        elif isinstance(obj, CallbackQuery):
            obj = obj.message.chat
        elif isinstance(obj, ChatMemberUpdated):
            obj = obj.chat
        else:
            warnings.warn("ChatTypeFilter doesn't support %s as input", type(obj))
            return False

        return obj.type in self.chat_type
    
    
class MediaGroupFilter(BoundFilter):
    """
    Check if message is part of a media group.

    `is_media_group=True` - the message is part of a media group
    `is_media_group=False` - the message is NOT part of a media group
    """

    key = "is_media_group"

    def __init__(self, is_media_group: bool):
        self.is_media_group = is_media_group

    async def check(self, message: types.Message) -> bool:
        return bool(getattr(message, "media_group_id")) is self.is_media_group
