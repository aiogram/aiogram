from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Literal, Optional, cast

from aioredis import ConnectionPool, Redis

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StateType, StorageKey

DEFAULT_REDIS_LOCK_KWARGS = {"timeout": 60}


class KeyBuilder(ABC):
    """
    Base class for Redis key builder
    """

    @abstractmethod
    def build(self, key: StorageKey, part: Literal["data", "state", "lock"]) -> str:
        pass


class DefaultKeyBuilder(KeyBuilder):
    """
    Simple Redis key builder with default prefix.

    Generates a colon-joined string with prefix, chat_id, user_id,
    optional bot_id and optional destiny.
    """

    def __init__(
        self, prefix: str = "fsm", with_bot_id: bool = False, with_destiny: bool = False
    ) -> None:
        self.prefix = prefix
        self.with_bot_id = with_bot_id
        self.with_destiny = with_destiny

    def build(self, key: StorageKey, part: Literal["data", "state", "lock"]) -> str:
        parts = [self.prefix]
        if self.with_bot_id:
            parts.append(str(key.bot_id))
        parts.extend([str(key.chat_id), str(key.user_id)])
        if self.with_destiny:
            parts.append(key.destiny)
        parts.append(part)
        return ":".join(parts)


class RedisStorage(BaseStorage):
    def __init__(
        self,
        redis: Redis,
        key_builder: Optional[KeyBuilder] = None,
        state_ttl: Optional[int] = None,
        data_ttl: Optional[int] = None,
        lock_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        if lock_kwargs is None:
            lock_kwargs = DEFAULT_REDIS_LOCK_KWARGS
        self.redis = redis
        self.key_builder = key_builder
        self.state_ttl = state_ttl
        self.data_ttl = data_ttl
        self.lock_kwargs = lock_kwargs

    @classmethod
    def from_url(
        cls, url: str, connection_kwargs: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> "RedisStorage":
        if connection_kwargs is None:
            connection_kwargs = {}
        pool = ConnectionPool.from_url(url, **connection_kwargs)
        redis = Redis(connection_pool=pool)
        return cls(redis=redis, **kwargs)

    async def close(self) -> None:
        await self.redis.close()  # type: ignore

    @asynccontextmanager
    async def lock(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> AsyncGenerator[None, None]:
        redis_key = self.key_builder.build(key, "lock")
        async with self.redis.lock(name=redis_key, **self.lock_kwargs):
            yield None

    async def set_state(
        self,
        bot: Bot,
        key: StorageKey,
        state: StateType = None,
    ) -> None:
        redis_key = self.key_builder.build(key, "state")
        if state is None:
            await self.redis.delete(redis_key)
        else:
            await self.redis.set(
                redis_key,
                state.state if isinstance(state, State) else state,  # type: ignore[arg-type]
                ex=self.state_ttl,  # type: ignore[arg-type]
            )

    async def get_state(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> Optional[str]:
        redis_key = self.key_builder.build(key, "state")
        value = await self.redis.get(redis_key)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return cast(Optional[str], value)

    async def set_data(
        self,
        bot: Bot,
        key: StorageKey,
        data: Dict[str, Any],
    ) -> None:
        redis_key = self.key_builder.build(key, "data")
        if not data:
            await self.redis.delete(redis_key)
            return
        await self.redis.set(
            redis_key,
            bot.session.json_dumps(data),
            ex=self.data_ttl,  # type: ignore[arg-type]
        )

    async def get_data(
        self,
        bot: Bot,
        key: StorageKey,
    ) -> Dict[str, Any]:
        redis_key = self.key_builder.build(key, "data")
        value = await self.redis.get(redis_key)
        if value is None:
            return {}
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return cast(Dict[str, Any], bot.session.json_loads(value))
