from __future__ import annotations

import io
import logging
import typing
import warnings
from typing import TypeVar

from babel.support import LazyProxy

from .fields import BaseField
from ..utils import json
from ..utils.exceptions import AIOGramWarning
from ..utils.mixins import ContextInstanceMixin
if typing.TYPE_CHECKING:
    from ..bot.bot import Bot

__all__ = ('MetaTelegramObject', 'TelegramObject', 'InputFile', 'String', 'Integer', 'Float', 'Boolean')

PROPS_ATTR_NAME = '_props'
VALUES_ATTR_NAME = '_values'
ALIASES_ATTR_NAME = '_aliases'

# Binding of builtin types
InputFile = TypeVar('InputFile', 'InputFile', io.BytesIO, io.FileIO, str)
String = TypeVar('String', bound=str)
Integer = TypeVar('Integer', bound=int)
Float = TypeVar('Float', bound=float)
Boolean = TypeVar('Boolean', bound=bool)
T = TypeVar('T')

# Main aiogram logger
log = logging.getLogger('aiogram')


class MetaTelegramObject(type):
    """
    Metaclass for telegram objects
    """
    _objects = {}

    def __new__(mcs: typing.Type[T], name: str, bases: typing.Tuple[typing.Type], namespace: typing.Dict[str, typing.Any], **kwargs: typing.Any) -> T:
        cls = super(MetaTelegramObject, mcs).__new__(mcs, name, bases, namespace)

        props = {}
        values = {}
        aliases = {}

        # Get props, values, aliases from parent objects
        for base in bases:
            if not isinstance(base, MetaTelegramObject):
                continue
            props.update(getattr(base, PROPS_ATTR_NAME))
            # values.update(getattr(base, VALUES_ATTR_NAME))
            aliases.update(getattr(base, ALIASES_ATTR_NAME))

        # Scan current object for props
        for name, prop in ((name, prop) for name, prop in namespace.items() if isinstance(prop, BaseField)):
            props[prop.alias] = prop
            if prop.default is not None:
                values[prop.alias] = prop.default
            aliases[name] = prop.alias

        # Set attributes
        setattr(cls, PROPS_ATTR_NAME, props)
        # setattr(cls, VALUES_ATTR_NAME, values)
        setattr(cls, ALIASES_ATTR_NAME, aliases)

        mcs._objects[cls.__name__] = cls

        return cls

    @property
    def telegram_types(cls):
        return cls._objects


class TelegramObject(ContextInstanceMixin, metaclass=MetaTelegramObject):
    """
    Abstract class for telegram objects
    """

    def __init__(self, conf: typing.Dict[str, typing.Any] = None, **kwargs: typing.Any) -> None:
        """
        Deserialize object

        :param conf:
        :param kwargs:
        """
        if conf is None:
            conf = {}
        self._conf = conf

        # Load data
        for key, value in kwargs.items():
            if key in self.props:
                self.props[key].set_value(self, value, parent=self)
            else:
                self.values[key] = value

        # Load default values
        for key, value in self.props.items():
            if value.default and key not in self.values:
                self.values[key] = value.default

    @property
    def conf(self) -> typing.Dict[str, typing.Any]:
        return self._conf

    @property
    def props(self) -> typing.Dict[str, BaseField]:
        """
        Get props

        :return: dict with props
        """
        return getattr(self, PROPS_ATTR_NAME, {})

    @property
    def props_aliases(self) -> typing.Dict[str, str]:
        """
        Get aliases for props

        :return:
        """
        return getattr(self, ALIASES_ATTR_NAME, {})

    @property
    def values(self) -> typing.Dict[str, typing.Any]:
        """
        Get values

        :return:
        """
        if not hasattr(self, VALUES_ATTR_NAME):
            setattr(self, VALUES_ATTR_NAME, {})
        return getattr(self, VALUES_ATTR_NAME)

    @property
    def telegram_types(self) -> typing.List[TelegramObject]:
        return type(self).telegram_types

    @classmethod
    def to_object(cls: typing.Type[T],
                  data: typing.Dict[str, typing.Any],
                  conf: typing.Dict[str, typing.Any] = None
                  ) -> T:
        """
        Deserialize object

        :param data:
        :param conf:
        :return:
        """
        return cls(conf=conf, **data)

    @property
    def bot(self) -> Bot:
        from ..bot.bot import Bot

        bot = Bot.get_current()
        if bot is None:
            raise RuntimeError("Can't get bot instance from context. "
                               "You can fix it with setting current instance: "
                               "'Bot.set_current(bot_instance)'")
        return bot

    def to_python(self) -> typing.Dict[str, typing.Any]:
        """
        Get object as JSON serializable

        :return:
        """
        result = {}
        for name, value in self.values.items():
            if value is None:
                continue
            if name in self.props:
                value = self.props[name].export(self)
            if isinstance(value, TelegramObject):
                value = value.to_python()
            if isinstance(value, LazyProxy):
                value = str(value)
            result[self.props_aliases.get(name, name)] = value
        return result

    def clean(self) -> None:
        """
        Remove empty values
        """
        for key, value in self.values.copy().items():
            if value is None:
                del self.values[key]

    def as_json(self) -> str:
        """
        Get object as JSON string

        :return: JSON
        :rtype: :obj:`str`
        """
        return json.dumps(self.to_python())

    @classmethod
    def create(cls: typing.Type[T], *args: typing.Any, **kwargs: typing.Any) -> T:
        raise NotImplemented

    def __str__(self) -> str:
        """
        Return object as string. Alias for '.as_json()'

        :return: str
        """
        return self.as_json()

    def __repr__(self) -> str:
        """
        Return object readable representation.

        Example: <ObjectName {"id": 123456}>
        :return: object class name and object data as a string
        """
        return f"<{type(self).__name__} {self}>"

    def __getitem__(self, item: typing.Union[str, int]) -> typing.Any:
        """
        Item getter (by key)

        :param item:
        :return:
        """
        if item in self.props:
            return self.props[item].get_value(self)
        return self.values[item]

    def __setitem__(self, key: str, value: typing.Any) -> None:
        """
        Item setter (by key)

        :param key:
        :param value:
        :return:
        """
        if key in self.props:
            return self.props[key].set_value(self, value, self.conf.get('parent', self))
        self.values[key] = value

        # Show warning when Telegram silently adds new Fields
        warnings.warn(f"Bot API Field {key!r} is not defined in {self.__class__!r} class.\n"
                      "Bot API has been updated. Check for updates at https://telegram.org/blog and "
                      "https://github.com/aiogram/aiogram/releases", AIOGramWarning)

    def __contains__(self, item: str) -> bool:
        """
        Check key contains in that object

        :param item:
        :return:
        """
        # self.clean()
        return bool(self.values.get(item, None))

    def __iter__(self) -> typing.Iterator[str]:
        """
        Iterate over items

        :return:
        """
        yield from self.to_python().items()

    def iter_keys(self) -> typing.Generator[typing.Any, None, None]:
        """
        Iterate over keys

        :return:
        """
        for key, _ in self:
            yield key

    def iter_values(self) -> typing.Generator[typing.Any, None, None]:
        """
        Iterate over values

        :return:
        """
        for _, value in self:
            yield value

    def __hash__(self) -> int:
        def _hash(obj) -> int:
            buf: int = 0
            if isinstance(obj, list):
                for item in obj:
                    buf += _hash(item)
            elif isinstance(obj, dict):
                for dict_key, dict_value in obj.items():
                    buf += hash(dict_key) + _hash(dict_value)
            else:
                try:
                    buf += hash(obj)
                except TypeError:  # Skip unhashable objects
                    pass
            return buf

        result = 0
        for key, value in sorted(self.values.items()):
            result += hash(key) + _hash(value)

        return result

    def __eq__(self, other: TelegramObject) -> bool:
        return isinstance(other, self.__class__) and hash(other) == hash(self)
