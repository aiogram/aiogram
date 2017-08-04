"""
This module has redis storage for finite-state machine based on `aioredis <https://github.com/aio-libs/aioredis>`_ driver
"""

import typing

import aioredis

from aiogram.utils import json
from ...dispatcher.storage import BaseStorage


class RedisStorage(BaseStorage):
    """
    Simple Redis-base storage for FSM.

    Usage:

    .. code-block:: python3

        storage = RedisStorage('localhost', 6379, db=5)
        dp = Dispatcher(bot, storage=storage)

    """

    def __init__(self, host, port, db=None, password=None, ssl=None, loop=None, **kwargs):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._loop = loop
        self._kwargs = kwargs

        self._redis: aioredis.RedisConnection = None

    @property
    async def redis(self) -> aioredis.RedisConnection:
        """
        Get Redis connection

        This property is awaitable.
        """
        if self._redis is None:
            self._redis = await aioredis.create_connection((self._host, self._port),
                                                           db=self._db, password=self._password, ssl=self._ssl,
                                                           loop=self._loop,
                                                           **self._kwargs)
        return self._redis

    async def get_record(self, *,
                         chat: typing.Union[str, int, None] = None,
                         user: typing.Union[str, int, None] = None) -> typing.Dict:
        """
        Get record from storage

        :param chat:
        :param user:
        :return:
        """
        chat, user = self.check_address(chat=chat, user=user)
        addr = f"{chat}:{user}"

        conn = await self.redis
        data = await conn.execute('GET', addr)
        if data is None:
            return {'state': None, 'data': {}}
        return json.loads(data)

    async def set_record(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         state=None, data=None):
        """
        Write record to storage

        :param chat:
        :param user:
        :param state:
        :param data:
        :return:
        """
        if data is None:
            data = {}

        chat, user = self.check_address(chat=chat, user=user)
        addr = f"{chat}:{user}"

        record = {'state': state, 'data': data}

        conn = await self.redis
        await conn.execute('SET', addr, json.dumps(record))

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        record = await self.get_record(chat=chat, user=user)
        return record['state']

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        record = await self.get_record(chat=chat, user=user)
        return record['data']

    async def set_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        record = await self.get_record(chat=chat, user=user)
        await self.set_record(chat=chat, user=user, state=state, data=record['data'])

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        record = await self.get_record(chat=chat, user=user)
        await self.set_record(chat=chat, user=user, state=record['state'], data=data)

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        data = await self.get_data(chat=chat, user=user)
        if data is None:
            data = []
        data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=data)
