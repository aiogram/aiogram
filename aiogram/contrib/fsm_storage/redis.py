"""
This module has redis storage for finite-state machine based on `aioredis <https://github.com/aio-libs/aioredis>`_ driver
"""

import asyncio
import typing

import aioredis

from ...dispatcher.storage import BaseStorage
from ...utils import json


class RedisStorage(BaseStorage):
    """
    Simple Redis-base storage for FSM.

    Usage:

    .. code-block:: python3

        storage = RedisStorage('localhost', 6379, db=5)
        dp = Dispatcher(bot, storage=storage)

    And need to close Redis connection when shutdown

    .. code-block:: python3

        await dp.storage.close()
        await dp.storage.wait_closed()

    """

    def __init__(self, host='localhost', port=6379, db=None, password=None, ssl=None, loop=None, **kwargs):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._loop = loop or asyncio.get_event_loop()
        self._kwargs = kwargs

        self._redis: aioredis.RedisConnection = None
        self._connection_lock = asyncio.Lock(loop=self._loop)

    async def close(self):
        if self._redis and not self._redis.closed:
            self._redis.close()
            del self._redis
            self._redis = None

    async def wait_closed(self):
        if self._redis:
            return await self._redis.wait_closed()
        return True

    @property
    async def redis(self) -> aioredis.RedisConnection:
        """
        Get Redis connection

        This property is awaitable.
        """
        # Use thread-safe asyncio Lock because this method without that is not safe
        async with self._connection_lock:
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
        addr = f"fsm:{chat}:{user}"

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
        addr = f"fsm:{chat}:{user}"

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
        record = await self.get_record(chat=chat, user=user)
        record_data = record.get('data', {})
        record_data.update(data, **kwargs)
        await self.set_record(chat=chat, user=user, state=record['state'], data=record_data)

    async def get_states_list(self) -> typing.List[typing.Tuple[int]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.redis
        result = []

        keys = await conn.execute('KEYS', 'fsm:*')
        for item in keys:
            *_, chat, user = item.decode('utf-8').split(':')
            result.append((chat, user))

        return result

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        conn = await self.redis

        if full:
            conn.execute('FLUSHDB')
        else:
            keys = await conn.execute('KEYS', 'fsm:*')
            conn.execute('DEL', *keys)
