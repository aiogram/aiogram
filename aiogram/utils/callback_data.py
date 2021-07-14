"""
Callback data factory

Usage:
    Create instance of factory with prefix and element names:
    >>> posts_query = CallbackData('post', 'post_id', 'action')

    Then you can generate callback data:
    >>> posts_query.new('32feff9b-92fa-48d9-9d29-621dc713743a', action='view')
    <<< post:32feff9b-92fa-48d9-9d29-621dc713743a:view

    Also you can generate filters:
    >>> posts_query.filter(action='delete')
    This filter can handle callback data by pattern: post:*:delete
"""
from __future__ import annotations

import typing

from aiogram import types
from aiogram.dispatcher.filters import Filter


class CallbackData:
    """
    Callback data factory
    """

    def __init__(self, prefix, *parts, sep=':'):
        if not isinstance(prefix, str):
            raise TypeError(f'Prefix must be instance of str not {type(prefix).__name__}')
        if not prefix:
            raise ValueError("Prefix can't be empty")
        if sep in prefix:
            raise ValueError(f"Separator {sep!r} can't be used in prefix")
        if not parts:
            raise TypeError('Parts were not passed!')

        self.prefix = prefix
        self.sep = sep

        self._part_names = parts

    def new(self, *args, **kwargs) -> str:
        """
        Generate callback data

        :param args:
        :param kwargs:
        :return:
        """
        args = list(args)

        data = [self.prefix]

        for part in self._part_names:
            value = kwargs.pop(part, None)
            if value is None:
                if args:
                    value = args.pop(0)
                else:
                    raise ValueError(f'Value for {part!r} was not passed!')

            if value is not None and not isinstance(value, str):
                value = str(value)

            if not value:
                raise ValueError(f"Value for part {part!r} can't be empty!'")
            if self.sep in value:
                raise ValueError(f"Symbol {self.sep!r} is defined as the separator and can't be used in parts' values")

            data.append(value)

        if args or kwargs:
            raise TypeError('Too many arguments were passed!')

        callback_data = self.sep.join(data)
        if len(callback_data.encode()) > 64:
            raise ValueError('Resulted callback data is too long!')

        return callback_data

    def parse(self, callback_data: str) -> typing.Dict[str, str]:
        """
        Parse data from the callback data

        :param callback_data:
        :return:
        """
        prefix, *parts = callback_data.split(self.sep)
        if prefix != self.prefix:
            raise ValueError("Passed callback data can't be parsed with that prefix.")
        elif len(parts) != len(self._part_names):
            raise ValueError('Invalid parts count!')

        result = {'@': prefix}
        result.update(zip(self._part_names, parts))
        return result

    def filter(self, **config) -> CallbackDataFilter:
        """
        Generate filter

        :param config:
        :return:
        """
        for key in config.keys():
            if key not in self._part_names:
                raise ValueError(f'Invalid field name {key!r}')
        return CallbackDataFilter(self, config)


class CallbackDataFilter(Filter):

    def __init__(self, factory: CallbackData, config: typing.Dict[str, str]):
        self.config = config
        self.factory = factory

    @classmethod
    def validate(cls, full_config: typing.Dict[str, typing.Any]):
        raise ValueError("That filter can't be used in filters factory!")

    async def check(self, query: types.CallbackQuery):
        try:
            data = self.factory.parse(query.data)
        except ValueError:
            return False

        for key, value in self.config.items():
            if isinstance(value, (list, tuple, set, frozenset)):
                if data.get(key) not in value:
                    return False
            elif data.get(key) != value:
                return False
        return {'callback_data': data}
