import json
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Optional, cast

from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool
from redis.asyncio.lock import Lock
from redis.typing import ExpiryT

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import (
    BaseEventIsolation,
    BaseStorage,
    DefaultKeyBuilder,
    KeyBuilder,
    StateType,
    StorageKey,
)

DEFAULT_REDIS_LOCK_KWARGS = {"timeout": 60}
_JsonLoads = Callable[..., Any]
_JsonDumps = Callable[..., str]


class RedisStorage(BaseStorage):
    """
    Redis storage required :code:`redis` package installed (:code:`pip install redis`)
    """

    def __init__(
        self,
        redis: Redis,
        key_builder: Optional[KeyBuilder] = None,
        state_ttl: Optional[ExpiryT] = None,
        data_ttl: Optional[ExpiryT] = None,
        json_loads: _JsonLoads = json.loads,
        json_dumps: _JsonDumps = json.dumps,
    ) -> None:
        """
        :param redis: Instance of Redis connection
        :param key_builder: builder that helps to convert contextual key to string
        :param state_ttl: TTL for state records
        :param data_ttl: TTL for data records
        """
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        self.redis = redis
        self.key_builder = key_builder
        self.state_ttl = state_ttl
        self.data_ttl = data_ttl
        self.json_loads = json_loads
        self.json_dumps = json_dumps

    @classmethod
    def from_url(
        cls, url: str, connection_kwargs: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> "RedisStorage":
        """
        Create an instance of :class:`RedisStorage` with specifying the connection string

        :param url: for example :code:`redis://user:password@host:port/db`
        :param connection_kwargs: see :code:`redis` docs
        :param kwargs: arguments to be passed to :class:`RedisStorage`
        :return: an instance of :class:`RedisStorage`
        """
        if connection_kwargs is None:
            connection_kwargs = {}
        pool = ConnectionPool.from_url(url, **connection_kwargs)
        redis = Redis(connection_pool=pool)
        return cls(redis=redis, **kwargs)

    def create_isolation(self, **kwargs: Any) -> "RedisEventIsolation":
        return RedisEventIsolation(redis=self.redis, key_builder=self.key_builder, **kwargs)

    async def close(self) -> None:
        await self.redis.aclose(close_connection_pool=True)

    async def set_state(
        self,
        key: StorageKey,
        state: StateType = None,
    ) -> None:
        redis_key = self.key_builder.build(key, "state")
        if state is None:
            await self.redis.delete(redis_key)
        else:
            await self.redis.set(
                redis_key,
                cast(str, state.state if isinstance(state, State) else state),
                ex=self.state_ttl,
            )

    async def get_state(
        self,
        key: StorageKey,
    ) -> Optional[str]:
        redis_key = self.key_builder.build(key, "state")
        value = await self.redis.get(redis_key)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return cast(Optional[str], value)

    async def set_data(
        self,
        key: StorageKey,
        data: Dict[str, Any],
    ) -> None:
        redis_key = self.key_builder.build(key, "data")
        if not data:
            await self.redis.delete(redis_key)
            return
        await self.redis.set(
            redis_key,
            self.json_dumps(data),
            ex=self.data_ttl,
        )

    async def get_data(
        self,
        key: StorageKey,
    ) -> Dict[str, Any]:
        redis_key = self.key_builder.build(key, "data")
        value = await self.redis.get(redis_key)
        if value is None:
            return {}
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return cast(Dict[str, Any], self.json_loads(value))


class RedisEventIsolation(BaseEventIsolation):
    def __init__(
        self,
        redis: Redis,
        key_builder: Optional[KeyBuilder] = None,
        lock_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        if lock_kwargs is None:
            lock_kwargs = DEFAULT_REDIS_LOCK_KWARGS
        self.redis = redis
        self.key_builder = key_builder
        self.lock_kwargs = lock_kwargs

    @classmethod
    def from_url(
        cls,
        url: str,
        connection_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "RedisEventIsolation":
        if connection_kwargs is None:
            connection_kwargs = {}
        pool = ConnectionPool.from_url(url, **connection_kwargs)
        redis = Redis(connection_pool=pool)
        return cls(redis=redis, **kwargs)

    @asynccontextmanager
    async def lock(
        self,
        key: StorageKey,
    ) -> AsyncGenerator[None, None]:
        redis_key = self.key_builder.build(key, "lock")
        async with self.redis.lock(name=redis_key, **self.lock_kwargs, lock_class=Lock):
            yield None

    async def close(self) -> None:
        pass
