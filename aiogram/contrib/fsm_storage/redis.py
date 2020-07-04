"""
This module has redis storage for finite-state machine
    based on `aioredis <https://github.com/aio-libs/aioredis>`_ driver
"""

import asyncio
import logging
import typing

import aioredis

from ...dispatcher.storage import BaseStorage
from ...utils import json

STATE_KEY = 'state'
STATE_DATA_KEY = 'data'
STATE_BUCKET_KEY = 'bucket'


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
    def __init__(self, host='localhost', port=6379, db=None,
                 password=None, ssl=None, loop=None, **kwargs):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._loop = loop or asyncio.get_event_loop()
        self._kwargs = kwargs

        self._redis: typing.Optional[aioredis.RedisConnection] = None
        self._connection_lock = asyncio.Lock(loop=self._loop)

    async def close(self):
        async with self._connection_lock:
            if self._redis and not self._redis.closed:
                self._redis.close()

    async def wait_closed(self):
        async with self._connection_lock:
            if self._redis:
                return await self._redis.wait_closed()
            return True

    async def redis(self) -> aioredis.RedisConnection:
        """
        Get Redis connection
        """
        # Use thread-safe asyncio Lock because this method without that is not safe
        async with self._connection_lock:
            if self._redis is None or self._redis.closed:
                self._redis = await aioredis.create_connection((self._host, self._port),
                                                               db=self._db, password=self._password, ssl=self._ssl,
                                                               loop=self._loop,
                                                               **self._kwargs)
        return self._redis

    async def get_record(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None) -> typing.Dict:
        """
        Get record from storage

        :param chat_id:
        :param user_id:
        :return:
        """
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        addr = f"fsm:{chat_id}:{user_id}"

        conn = await self.redis()
        data = await conn.execute('GET', addr)
        if data is None:
            return {'state': None, 'data': {}}
        return json.loads(data)

    async def set_record(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         state=None, data=None, bucket=None):
        """
        Write record to storage

        :param bucket:
        :param chat_id:
        :param user_id:
        :param state:
        :param data:
        :return:
        """
        if data is None:
            data = {}
        if bucket is None:
            bucket = {}

        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        addr = f"fsm:{chat_id}:{user_id}"

        record = {'state': state, 'data': data, 'bucket': bucket}

        conn = await self.redis()
        await conn.execute('SET', addr, json.dumps(record))

    async def get_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        return record['state']

    async def get_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        return record['data']

    async def set_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        await self.set_record(chat_id=chat_id, user_id=user_id, state=state, data=record['data'])

    async def set_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        await self.set_record(chat_id=chat_id, user_id=user_id, state=record['state'], data=data)

    async def update_data(self, *,
                          chat_id: typing.Union[str, int, None] = None,
                          user_id: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        if data is None:
            data = {}
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        record_data = record.get('data', {})
        record_data.update(data, **kwargs)
        await self.set_record(chat_id=chat_id, user_id=user_id, state=record['state'], data=record_data)

    async def get_states_list(self) -> typing.List[typing.Tuple[str, str]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.redis()
        result = []

        keys = await conn.execute('KEYS', 'fsm:*')
        for item in keys:
            *_, chat_id, user_id = item.decode('utf-8').split(':')
            result.append((chat_id, user_id))

        return result

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        conn = await self.redis()

        if full:
            await conn.execute('FLUSHDB')
        else:
            keys = await conn.execute('KEYS', 'fsm:*')
            await conn.execute('DEL', *keys)

    def has_bucket(self):
        return True

    async def get_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         default: typing.Optional[str] = None) -> typing.Dict:
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        return record.get('bucket', {})

    async def set_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        await self.set_record(chat_id=chat_id, user_id=user_id, state=record['state'], data=record['data'], bucket=bucket)

    async def update_bucket(self, *,
                            chat_id: typing.Union[str, int, None] = None,
                            user_id: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None, **kwargs):
        record = await self.get_record(chat_id=chat_id, user_id=user_id)
        record_bucket = record.get('bucket', {})
        if bucket is None:
            bucket = {}
        record_bucket.update(bucket, **kwargs)
        await self.set_record(chat_id=chat_id, user_id=user_id, state=record['state'], data=record_bucket, bucket=bucket)


class RedisStorage2(BaseStorage):
    """
    Busted Redis-base storage for FSM.
    Works with Redis connection pool and customizable keys prefix.

    Usage:

    .. code-block:: python3

        storage = RedisStorage('localhost', 6379, db=5, pool_size=10, prefix='my_fsm_key')
        dp = Dispatcher(bot, storage=storage)

    And need to close Redis connection when shutdown

    .. code-block:: python3

        await dp.storage.close()
        await dp.storage.wait_closed()

    """
    def __init__(self, host: str = 'localhost', port=6379, db=None, password=None, 
                 ssl=None, pool_size=10, loop=None, prefix='fsm',
                 state_ttl: int = 0,
                 data_ttl: int = 0,
                 bucket_ttl: int = 0,
                 **kwargs):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._pool_size = pool_size
        self._loop = loop or asyncio.get_event_loop()
        self._kwargs = kwargs
        self._prefix = (prefix,)

        self._state_ttl = state_ttl
        self._data_ttl = data_ttl
        self._bucket_ttl = bucket_ttl

        self._redis: typing.Optional[aioredis.RedisConnection] = None
        self._connection_lock = asyncio.Lock(loop=self._loop)

    async def redis(self) -> aioredis.Redis:
        """
        Get Redis connection
        """
        # Use thread-safe asyncio Lock because this method without that is not safe
        async with self._connection_lock:
            if self._redis is None or self._redis.closed:
                self._redis = await aioredis.create_redis_pool((self._host, self._port),
                                                               db=self._db, password=self._password, ssl=self._ssl,
                                                               minsize=1, maxsize=self._pool_size,
                                                               loop=self._loop, **self._kwargs)
        return self._redis

    def generate_key(self, *parts):
        return ':'.join(self._prefix + tuple(map(str, parts)))

    async def close(self):
        async with self._connection_lock:
            if self._redis and not self._redis.closed:
                self._redis.close()

    async def wait_closed(self):
        async with self._connection_lock:
            if self._redis:
                return await self._redis.wait_closed()
            return True

    async def get_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        key = self.generate_key(chat_id, user_id, STATE_KEY)
        redis = await self.redis()
        return await redis.get(key, encoding='utf8') or None

    async def get_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       default: typing.Optional[dict] = None) -> typing.Dict:
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        key = self.generate_key(chat_id, user_id, STATE_DATA_KEY)
        redis = await self.redis()
        raw_result = await redis.get(key, encoding='utf8')
        if raw_result:
            return json.loads(raw_result)
        return default or {}

    async def set_state(self, *,
                        chat_id: typing.Union[str, int, None] = None,
                        user_id: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        key = self.generate_key(chat_id, user_id, STATE_KEY)
        redis = await self.redis()
        if state is None:
            await redis.delete(key)
        else:
            await redis.set(key, state, expire=self._state_ttl)

    async def set_data(self, *,
                       chat_id: typing.Union[str, int, None] = None,
                       user_id: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        key = self.generate_key(chat_id, user_id, STATE_DATA_KEY)
        redis = await self.redis()
        await redis.set(key, json.dumps(data), expire=self._data_ttl)

    async def update_data(self, *,
                          chat_id: typing.Union[str, int, None] = None,
                          user_id: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat_id=chat_id, user_id=user_id, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat_id=chat_id, user_id=user_id, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        key = self.generate_key(chat_id, user_id, STATE_BUCKET_KEY)
        redis = await self.redis()
        raw_result = await redis.get(key, encoding='utf8')
        if raw_result:
            return json.loads(raw_result)
        return default or {}

    async def set_bucket(self, *,
                         chat_id: typing.Union[str, int, None] = None,
                         user_id: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        chat_id, user_id = self.check_address(chat_id=chat_id, user_id=user_id)
        key = self.generate_key(chat_id, user_id, STATE_BUCKET_KEY)
        redis = await self.redis()
        await redis.set(key, json.dumps(bucket), expire=self._bucket_ttl)

    async def update_bucket(self, *,
                            chat_id: typing.Union[str, int, None] = None,
                            user_id: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None, **kwargs):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat_id=chat_id, user_id=user_id)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat_id=chat_id, user_id=user_id, bucket=temp_bucket)

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        conn = await self.redis()

        if full:
            await conn.flushdb()
        else:
            keys = await conn.keys(self.generate_key('*'))
            await conn.delete(*keys)

    async def get_states_list(self) -> typing.List[typing.Tuple[str, str]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.redis()
        result = []

        keys = await conn.keys(self.generate_key('*', '*', STATE_KEY), encoding='utf8')
        for item in keys:
            *_, chat_id, user_id, _ = item.split(':')
            result.append((chat_id, user_id))

        return result

    async def import_redis1(self, redis1):
        await migrate_redis1_to_redis2(redis1, self)


async def migrate_redis1_to_redis2(storage1: RedisStorage, storage2: RedisStorage2):
    """
    Helper for migrating from RedisStorage to RedisStorage2

    :param storage1: instance of RedisStorage
    :param storage2: instance of RedisStorage2
    :return:
    """
    if not isinstance(storage1, RedisStorage):  # better than assertion
        raise TypeError(f"{type(storage1)} is not RedisStorage instance.")
    if not isinstance(storage2, RedisStorage):
        raise TypeError(f"{type(storage2)} is not RedisStorage instance.")

    log = logging.getLogger('aiogram.RedisStorage')

    for chat_id, user_id in await storage1.get_states_list():
        state = await storage1.get_state(chat_id=chat_id, user_id=user_id)
        await storage2.set_state(chat_id=chat_id, user_id=user_id, state=state)

        data = await storage1.get_data(chat_id=chat_id, user_id=user_id)
        await storage2.set_data(chat_id=chat_id, user_id=user_id, data=data)

        bucket = await storage1.get_bucket(chat_id=chat_id, user_id=user_id)
        await storage2.set_bucket(chat_id=chat_id, user_id=user_id, bucket=bucket)

        log.info(f"Migrated user {user_id} in chat {chat_id}")
