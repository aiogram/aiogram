"""
This module has redis storage for finite-state machine based on `aioredis <https://github.com/aio-libs/aioredis>`_ driver
"""

import asyncio
import logging
import typing
from abc import ABC, abstractmethod

import aioredis

from ...dispatcher.storage import BaseStorage
from ...utils import json
from ...utils.deprecated import deprecated

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

    @deprecated("`RedisStorage` will be removed in aiogram v3.0. "
                "Use `RedisStorage2` instead.", stacklevel=3)
    def __init__(self, host='localhost', port=6379, db=None, password=None, ssl=None, loop=None, **kwargs):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._kwargs = kwargs

        self._redis: typing.Optional["aioredis.RedisConnection"] = None
        self._connection_lock = asyncio.Lock()

    async def close(self):
        async with self._connection_lock:
            if self._redis and not self._redis.closed:
                self._redis.close()

    async def wait_closed(self):
        async with self._connection_lock:
            if self._redis:
                return await self._redis.wait_closed()
            return True

    async def redis(self) -> "aioredis.RedisConnection":
        """
        Get Redis connection
        """
        # Use thread-safe asyncio Lock because this method without that is not safe
        async with self._connection_lock:
            if self._redis is None or self._redis.closed:
                self._redis = await aioredis.create_connection((self._host, self._port),
                                                               db=self._db, password=self._password, ssl=self._ssl,
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

        conn = await self.redis()
        data = await conn.execute('GET', addr)
        if data is None:
            return {'state': None, 'data': {}}
        return json.loads(data)

    async def set_record(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         state=None, data=None, bucket=None):
        """
        Write record to storage

        :param bucket:
        :param chat:
        :param user:
        :param state:
        :param data:
        :return:
        """
        if data is None:
            data = {}
        if bucket is None:
            bucket = {}

        chat, user = self.check_address(chat=chat, user=user)
        addr = f"fsm:{chat}:{user}"

        conn = await self.redis()
        if state is None and data == bucket == {}:
            await conn.execute('DEL', addr)
        else:
            record = {'state': state, 'data': data, 'bucket': bucket}
            await conn.execute('SET', addr, json.dumps(record))

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        record = await self.get_record(chat=chat, user=user)
        return record.get('state', self.resolve_state(default))

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       default: typing.Optional[str] = None) -> typing.Dict:
        record = await self.get_record(chat=chat, user=user)
        return record['data']

    async def set_state(self, *,
                        chat: typing.Union[str, int, None] = None,
                        user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        record = await self.get_record(chat=chat, user=user)
        state = self.resolve_state(state)
        await self.set_record(chat=chat, user=user, state=state, data=record['data'])

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        record = await self.get_record(chat=chat, user=user)
        await self.set_record(chat=chat, user=user, state=record['state'], data=data)

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        if data is None:
            data = {}
        record = await self.get_record(chat=chat, user=user)
        record_data = record.get('data', {})
        record_data.update(data, **kwargs)
        await self.set_record(chat=chat, user=user, state=record['state'], data=record_data)

    async def get_states_list(self) -> typing.List[typing.Tuple[str, str]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        conn = await self.redis()
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
        conn = await self.redis()

        if full:
            await conn.execute('FLUSHDB')
        else:
            keys = await conn.execute('KEYS', 'fsm:*')
            await conn.execute('DEL', *keys)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         default: typing.Optional[str] = None) -> typing.Dict:
        record = await self.get_record(chat=chat, user=user)
        return record.get('bucket', {})

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        record = await self.get_record(chat=chat, user=user)
        await self.set_record(chat=chat, user=user, state=record['state'], data=record['data'], bucket=bucket)

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None,
                            user: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None, **kwargs):
        record = await self.get_record(chat=chat, user=user)
        record_bucket = record.get('bucket', {})
        if bucket is None:
            bucket = {}
        record_bucket.update(bucket, **kwargs)
        await self.set_record(chat=chat, user=user, state=record['state'], data=record_bucket, bucket=bucket)


class AioRedisAdapterBase(ABC):
    """Base aioredis adapter class."""

    def __init__(
            self,
            host: str = "localhost",
            port: int = 6379,
            db: typing.Optional[int] = None,
            password: typing.Optional[str] = None,
            ssl: typing.Optional[bool] = None,
            pool_size: int = 10,
            loop: typing.Optional[asyncio.AbstractEventLoop] = None,
            prefix: str = "fsm",
            state_ttl: typing.Optional[int] = None,
            data_ttl: typing.Optional[int] = None,
            bucket_ttl: typing.Optional[int] = None,
            **kwargs,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._pool_size = pool_size
        self._kwargs = kwargs
        self._prefix = (prefix,)

        self._state_ttl = state_ttl
        self._data_ttl = data_ttl
        self._bucket_ttl = bucket_ttl

        self._redis: typing.Optional["aioredis.Redis"] = None
        self._connection_lock = asyncio.Lock()

    @abstractmethod
    async def get_redis(self) -> aioredis.Redis:
        """Get Redis connection."""
        pass

    async def close(self):
        """Grace shutdown."""
        pass

    async def wait_closed(self):
        """Wait for grace shutdown finishes."""
        pass

    async def set(self, name, value, ex=None, **kwargs):
        """Set the value at key ``name`` to ``value``."""
        if ex == 0:
            ex = None
        return await self._redis.set(name, value, ex=ex, **kwargs)

    async def get(self, name, **kwargs):
        """Return the value at key ``name`` or None."""
        return await self._redis.get(name, **kwargs)

    async def delete(self, *names):
        """Delete one or more keys specified by ``names``"""
        return await self._redis.delete(*names)

    async def keys(self, pattern, **kwargs):
        """Returns a list of keys matching ``pattern``."""
        return await self._redis.keys(pattern, **kwargs)

    async def flushdb(self):
        """Delete all keys in the current database."""
        return await self._redis.flushdb()


class AioRedisAdapterV1(AioRedisAdapterBase):
    """Redis adapter for aioredis v1."""

    async def get_redis(self) -> aioredis.Redis:
        """Get Redis connection."""
        async with self._connection_lock:  # to prevent race
            if self._redis is None or self._redis.closed:
                self._redis = await aioredis.create_redis_pool(
                    (self._host, self._port),
                    db=self._db,
                    password=self._password,
                    ssl=self._ssl,
                    minsize=1,
                    maxsize=self._pool_size,
                    **self._kwargs,
                )
        return self._redis

    async def close(self):
        async with self._connection_lock:
            if self._redis and not self._redis.closed:
                self._redis.close()

    async def wait_closed(self):
        async with self._connection_lock:
            if self._redis:
                return await self._redis.wait_closed()
            return True

    async def get(self, name, **kwargs):
        return await self._redis.get(name, encoding="utf8", **kwargs)

    async def set(self, name, value, ex=None, **kwargs):
        if ex == 0:
            ex = None
        return await self._redis.set(name, value, expire=ex, **kwargs)

    async def keys(self, pattern, **kwargs):
        """Returns a list of keys matching ``pattern``."""
        return await self._redis.keys(pattern, encoding="utf8", **kwargs)


class AioRedisAdapterV2(AioRedisAdapterBase):
    """Redis adapter for aioredis v2."""

    async def get_redis(self) -> aioredis.Redis:
        """Get Redis connection."""
        async with self._connection_lock:  # to prevent race
            if self._redis is None:
                self._redis = aioredis.Redis(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    password=self._password,
                    ssl=self._ssl,
                    max_connections=self._pool_size,
                    decode_responses=True,
                    **self._kwargs,
                )
        return self._redis


class RedisStorage2(BaseStorage):
    """
    Busted Redis-base storage for FSM.
    Works with Redis connection pool and customizable keys prefix.

    Usage:

    .. code-block:: python3

        storage = RedisStorage2('localhost', 6379, db=5, pool_size=10, prefix='my_fsm_key')
        dp = Dispatcher(bot, storage=storage)

    And need to close Redis connection when shutdown

    .. code-block:: python3

        await dp.storage.close()
        await dp.storage.wait_closed()

    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 6379,
            db: typing.Optional[int] = None,
            password: typing.Optional[str] = None,
            ssl: typing.Optional[bool] = None,
            pool_size: int = 10,
            loop: typing.Optional[asyncio.AbstractEventLoop] = None,
            prefix: str = "fsm",
            state_ttl: typing.Optional[int] = None,
            data_ttl: typing.Optional[int] = None,
            bucket_ttl: typing.Optional[int] = None,
            **kwargs,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._pool_size = pool_size
        self._kwargs = kwargs
        self._prefix = (prefix,)

        self._state_ttl = state_ttl
        self._data_ttl = data_ttl
        self._bucket_ttl = bucket_ttl

        self._redis: typing.Optional[AioRedisAdapterBase] = None
        self._connection_lock = asyncio.Lock()

    @deprecated("This method will be removed in aiogram v3.0. "
                "You should use your own instance of Redis.", stacklevel=3)
    async def redis(self) -> aioredis.Redis:
        adapter = await self._get_adapter()
        return await adapter.get_redis()

    async def _get_adapter(self) -> AioRedisAdapterBase:
        """Get adapter based on aioredis version."""
        if self._redis is None:
            redis_version = int(aioredis.__version__.split(".")[0])
            connection_data = dict(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                ssl=self._ssl,
                pool_size=self._pool_size,
                **self._kwargs,
            )
            if redis_version == 1:
                self._redis = AioRedisAdapterV1(**connection_data)
            elif redis_version == 2:
                self._redis = AioRedisAdapterV2(**connection_data)
            else:
                raise RuntimeError(f"Unsupported aioredis version: {redis_version}")
            await self._redis.get_redis()
        return self._redis

    def generate_key(self, *parts):
        return ':'.join(self._prefix + tuple(map(str, parts)))

    async def close(self):
        if self._redis:
            return await self._redis.close()

    async def wait_closed(self):
        if self._redis:
            await self._redis.wait_closed()
            self._redis = None

    async def get_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        default: typing.Optional[str] = None) -> typing.Optional[str]:
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_KEY)
        redis = await self._get_adapter()
        return await redis.get(key) or self.resolve_state(default)

    async def get_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_DATA_KEY)
        redis = await self._get_adapter()
        raw_result = await redis.get(key)
        if raw_result:
            return json.loads(raw_result)
        return default or {}

    async def set_state(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                        state: typing.Optional[typing.AnyStr] = None):
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_KEY)
        redis = await self._get_adapter()
        if state is None:
            await redis.delete(key)
        else:
            await redis.set(key, self.resolve_state(state), ex=self._state_ttl)

    async def set_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                       data: typing.Dict = None):
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_DATA_KEY)
        redis = await self._get_adapter()
        if data:
            await redis.set(key, json.dumps(data), ex=self._data_ttl)
        else:
            await redis.delete(key)

    async def update_data(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                          data: typing.Dict = None, **kwargs):
        if data is None:
            data = {}
        temp_data = await self.get_data(chat=chat, user=user, default={})
        temp_data.update(data, **kwargs)
        await self.set_data(chat=chat, user=user, data=temp_data)

    def has_bucket(self):
        return True

    async def get_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         default: typing.Optional[dict] = None) -> typing.Dict:
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_BUCKET_KEY)
        redis = await self._get_adapter()
        raw_result = await redis.get(key)
        if raw_result:
            return json.loads(raw_result)
        return default or {}

    async def set_bucket(self, *, chat: typing.Union[str, int, None] = None, user: typing.Union[str, int, None] = None,
                         bucket: typing.Dict = None):
        chat, user = self.check_address(chat=chat, user=user)
        key = self.generate_key(chat, user, STATE_BUCKET_KEY)
        redis = await self._get_adapter()
        if bucket:
            await redis.set(key, json.dumps(bucket), ex=self._bucket_ttl)
        else:
            await redis.delete(key)

    async def update_bucket(self, *, chat: typing.Union[str, int, None] = None,
                            user: typing.Union[str, int, None] = None,
                            bucket: typing.Dict = None, **kwargs):
        if bucket is None:
            bucket = {}
        temp_bucket = await self.get_bucket(chat=chat, user=user)
        temp_bucket.update(bucket, **kwargs)
        await self.set_bucket(chat=chat, user=user, bucket=temp_bucket)

    async def reset_all(self, full=True):
        """
        Reset states in DB

        :param full: clean DB or clean only states
        :return:
        """
        redis = await self._get_adapter()

        if full:
            await redis.flushdb()
        else:
            keys = await redis.keys(self.generate_key('*'))
            await redis.delete(*keys)

    async def get_states_list(self) -> typing.List[typing.Tuple[str, str]]:
        """
        Get list of all stored chat's and user's

        :return: list of tuples where first element is chat id and second is user id
        """
        redis = await self._get_adapter()
        result = []

        keys = await redis.keys(self.generate_key('*', '*', STATE_KEY))
        for item in keys:
            *_, chat, user, _ = item.split(':')
            result.append((chat, user))

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

    for chat, user in await storage1.get_states_list():
        state = await storage1.get_state(chat=chat, user=user)
        await storage2.set_state(chat=chat, user=user, state=state)

        data = await storage1.get_data(chat=chat, user=user)
        await storage2.set_data(chat=chat, user=user, data=data)

        bucket = await storage1.get_bucket(chat=chat, user=user)
        await storage2.set_bucket(chat=chat, user=user, bucket=bucket)

        log.info(f"Migrated user {user} in chat {chat}")
