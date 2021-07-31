from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Union, cast

from aioredis import ConnectionPool, Redis

from aiogram import Bot
from aiogram.dispatcher.fsm.state import State
from aiogram.dispatcher.fsm.storage.base import BaseStorage, StateType

PrefixFactoryType = Callable[[Bot], str]
STATE_KEY = "state"
STATE_DATA_KEY = "data"
STATE_LOCK_KEY = "lock"

DEFAULT_REDIS_LOCK_KWARGS = {"timeout": 60}


class RedisStorage(BaseStorage):
    def __init__(
        self,
        redis: Redis,
        prefix: str = "fsm",
        prefix_bot: Union[bool, PrefixFactoryType, Dict[int, str]] = False,
        state_ttl: Optional[int] = None,
        data_ttl: Optional[int] = None,
        lock_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        if lock_kwargs is None:
            lock_kwargs = DEFAULT_REDIS_LOCK_KWARGS
        self.redis = redis
        self.prefix = prefix
        self.prefix_bot = prefix_bot
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

    def generate_key(self, bot: Bot, *parts: Any) -> str:
        prefix_parts = [self.prefix]
        if self.prefix_bot:
            if isinstance(self.prefix_bot, dict):
                prefix_parts.append(self.prefix_bot[bot.id])
            elif callable(self.prefix_bot):
                prefix_parts.append(self.prefix_bot(bot))
            else:
                prefix_parts.append(str(bot.id))
        prefix_parts.extend(parts)
        return ":".join(map(str, prefix_parts))

    @asynccontextmanager
    async def lock(self, bot: Bot, chat_id: int, user_id: int) -> AsyncGenerator[None, None]:
        key = self.generate_key(bot, chat_id, user_id, STATE_LOCK_KEY)
        async with self.redis.lock(name=key, **self.lock_kwargs):
            yield None

    async def set_state(
        self, bot: Bot, chat_id: int, user_id: int, state: StateType = None
    ) -> None:
        key = self.generate_key(bot, chat_id, user_id, STATE_KEY)
        if state is None:
            await self.redis.delete(key)
        else:
            await self.redis.set(
                key, state.state if isinstance(state, State) else state, ex=self.state_ttl  # type: ignore[arg-type]
            )

    async def get_state(self, bot: Bot, chat_id: int, user_id: int) -> Optional[str]:
        key = self.generate_key(bot, chat_id, user_id, STATE_KEY)
        value = await self.redis.get(key)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return cast(Optional[str], value)

    async def set_data(self, bot: Bot, chat_id: int, user_id: int, data: Dict[str, Any]) -> None:
        key = self.generate_key(bot, chat_id, user_id, STATE_DATA_KEY)
        if not data:
            await self.redis.delete(key)
            return
        json_data = bot.session.json_dumps(data)
        await self.redis.set(key, json_data, ex=self.data_ttl)  # type: ignore[arg-type]

    async def get_data(self, bot: Bot, chat_id: int, user_id: int) -> Dict[str, Any]:
        key = self.generate_key(bot, chat_id, user_id, STATE_DATA_KEY)
        value = await self.redis.get(key)
        if value is None:
            return {}
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return cast(Dict[str, Any], bot.session.json_loads(value))
