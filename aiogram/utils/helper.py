"""
Example:
    >>> from aiogram.utils.helper import Helper, ListItem, HelperMode, Item
    >>> class MyHelper(Helper):
    ...     mode = HelperMode.lowerCamelCase
    ...     FOO_ITEM = ListItem()
    ...     BAR_ITEM = ListItem()
    ...     BAZ_ITEM = ListItem()
    ...     LOREM = Item()
    ...
    >>> print(MyHelper.FOO_ITEM & MyHelper.BAR_ITEM)
    <<<  ['fooItem', 'barItem']
    >>> print(MyHelper.all())
    <<<  ['barItem', 'bazItem', 'fooItem', 'lorem']
"""
from typing import List

PROPS_KEYS_ATTR_NAME = '_props_keys'


class Helper:
    mode = ''

    @classmethod
    def all(cls):
        """
        Get all consts
        :return: list
        """
        result = []
        for name in dir(cls):
            if not name.isupper():
                continue
            value = getattr(cls, name)
            if isinstance(value, ItemsList):
                result.append(value[0])
            else:
                result.append(value)
        return result


class HelperMode(Helper):
    mode = 'original'

    SCREAMING_SNAKE_CASE = 'SCREAMING_SNAKE_CASE'
    lowerCamelCase = 'lowerCamelCase'
    CamelCase = 'CamelCase'
    snake_case = 'snake_case'
    lowercase = 'lowercase'

    @classmethod
    def all(cls):
        return [
            cls.SCREAMING_SNAKE_CASE,
            cls.lowerCamelCase,
            cls.CamelCase,
            cls.snake_case,
            cls.lowercase,
        ]

    @classmethod
    def _screaming_snake_case(cls, text):
        """
        Transform text to SCREAMING_SNAKE_CASE

        :param text:
        :return:
        """
        if text.isupper():
            return text
        result = ''
        for pos, symbol in enumerate(text):
            if symbol.isupper() and pos > 0:
                result += '_' + symbol
            else:
                result += symbol.upper()
        return result

    @classmethod
    def _snake_case(cls, text):
        """
        Transform text to snake case (Based on SCREAMING_SNAKE_CASE)

        :param text:
        :return:
        """
        if text.islower():
            return text
        return cls._screaming_snake_case(text).lower()

    @classmethod
    def _camel_case(cls, text, first_upper=False):
        """
        Transform text to camelCase or CamelCase

        :param text:
        :param first_upper: first symbol must be upper?
        :return:
        """
        result = ''
        need_upper = False
        for pos, symbol in enumerate(text):
            if symbol == '_' and pos > 0:
                need_upper = True
            else:
                result += symbol.upper() if need_upper else symbol.lower()
                need_upper = False
        if first_upper:
            result = result[0].upper() + result[1:]
        return result

    @classmethod
    def apply(cls, text, mode):
        """
        Apply mode for text

        :param text:
        :param mode:
        :return:
        """
        if mode == cls.SCREAMING_SNAKE_CASE:
            return cls._screaming_snake_case(text)
        if mode == cls.snake_case:
            return cls._snake_case(text)
        if mode == cls.lowercase:
            return cls._snake_case(text).replace('_', '')
        if mode == cls.lowerCamelCase:
            return cls._camel_case(text)
        if mode == cls.CamelCase:
            return cls._camel_case(text, True)
        if callable(mode):
            return mode(text)
        return text


class Item:
    """
    Helper item

    If a value is not provided,
    it will be automatically generated based on a variable's name
    """

    def __init__(self, value=None):
        self._value = value

    def __get__(self, instance, owner):
        return self._value

    def __set_name__(self, owner, name):
        if not name.isupper():
            raise NameError('Name for helper item must be in uppercase!')
        if not self._value:
            if hasattr(owner, 'mode'):
                self._value = HelperMode.apply(name, getattr(owner, 'mode'))


class ListItem(Item):
    """
    This item is always a list

    You can use &, | and + operators for that.
    """

    def add(self, other):
        return self + other

    def __get__(self, instance, owner):
        return ItemsList(self._value)

    def __getitem__(self, item):
        # Only for IDE. This method is never be called.
        return self._value

    # Need only for IDE
    __iadd__ = __add__ = __rand__ = __and__ = __ror__ = __or__ = add


class ItemsList(list):
    """
    Patch for default list

    This class provides +, &, |, +=, &=, |= operators for extending the list
    """

    def __init__(self, *seq):
        super(ItemsList, self).__init__(map(str, seq))

    def add(self, other):
        self.extend(other)
        return self

    __iadd__ = __add__ = __rand__ = __and__ = __ror__ = __or__ = add


class OrderedHelperMeta(type):

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)

        props_keys = [
            prop_name
            for prop_name in (
                name
                for name, prop in namespace.items()
                if isinstance(prop, (Item, ListItem))
            )
        ]

        setattr(cls, PROPS_KEYS_ATTR_NAME, props_keys)

        return cls


class OrderedHelper(metaclass=OrderedHelperMeta):
    mode = ''

    @classmethod
    def all(cls) -> List[str]:
        """
        Get all Items values
        """
        result = []
        for name in getattr(cls, PROPS_KEYS_ATTR_NAME, []):
            value = getattr(cls, name)
            if isinstance(value, ItemsList):
                result.append(value[0])
            else:
                result.append(value)
        return result
