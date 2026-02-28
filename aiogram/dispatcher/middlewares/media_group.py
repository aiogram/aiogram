import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, cast

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, TelegramObject

if TYPE_CHECKING:
    from redis.asyncio.client import Redis

DELAY_SEC = 1.0
TIMEOUT_SEC = 10
TTL_SEC = 600


class BaseMediaGroupAggregator(ABC):
    @abstractmethod
    async def add_into_group(self, media_group_id: str, media: Message) -> int:
        raise NotImplementedError

    @abstractmethod
    async def acquire_lock(self, media_group_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def release_lock(self, media_group_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_group(self, media_group_id: str) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    async def delete_group(self, media_group_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_last_message_time(self, media_group_id: str) -> float | None:
        raise NotImplementedError

    @staticmethod
    def deduplicate_messages(messages: list[Message]) -> list[Message]:
        message_ids = set()
        result = []
        for message in messages:
            if message.message_id in message_ids:
                continue
            result.append(message)
            message_ids.add(message.message_id)
        return result


class RedisMediaGroupAggregator(BaseMediaGroupAggregator):
    redis: "Redis"

    def __init__(self, redis: "Redis") -> None:
        self.redis = redis

    @staticmethod
    def get_group_key(media_group_id: str) -> str:
        return f"media_group:{media_group_id}:album"

    @staticmethod
    def get_last_message_time_key(media_group_id: str) -> str:
        return f"media_group:{media_group_id}:last_message_time"

    @staticmethod
    def get_group_lock_key(media_group_id: str) -> str:
        return f"media_group:{media_group_id}:lock"

    async def add_into_group(self, media_group_id: str, media: Message) -> int:
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(self.get_last_message_time_key(media_group_id), time.time(), ex=TTL_SEC)
            pipe.rpush(self.get_group_key(media_group_id), media.model_dump_json())
            pipe.expire(self.get_group_key(media_group_id), TTL_SEC)
            res = await pipe.execute()
        return cast(int, res[1])

    async def acquire_lock(self, media_group_id: str) -> bool:
        return cast(
            bool,
            await self.redis.set(
                self.get_group_lock_key(media_group_id), "1", nx=True, ex=TIMEOUT_SEC
            ),
        )

    async def release_lock(self, media_group_id: str) -> None:
        await self.redis.delete(self.get_group_lock_key(media_group_id))

    async def get_group(self, media_group_id: str) -> list[Message]:
        result = await self.redis.lrange(self.get_group_key(media_group_id), 0, -1)
        return self.deduplicate_messages([Message.model_validate_json(msg) for msg in result])

    async def delete_group(self, media_group_id: str) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(self.get_group_key(media_group_id))
            pipe.delete(self.get_last_message_time_key(media_group_id))
            await pipe.execute()

    async def get_last_message_time(self, media_group_id: str) -> float | None:
        result = await self.redis.get(self.get_last_message_time_key(media_group_id))
        if result is None:
            return None
        return float(result)


class MemoryMediaGroupAggregator(BaseMediaGroupAggregator):
    def __init__(self) -> None:
        self.groups: dict[str, list[Message]] = defaultdict(list)
        self.last_message_timers: dict[str, float] = {}
        self.locks: dict[str, bool] = {}

    async def add_into_group(self, media_group_id: str, media: Message) -> int:
        if media.message_id not in (msg.message_id for msg in self.groups[media_group_id]):
            self.groups[media_group_id].append(media)
        self.last_message_timers[media_group_id] = time.time()
        return len(self.groups[media_group_id])

    async def acquire_lock(self, media_group_id: str) -> bool:
        if self.locks.get(media_group_id):
            return False
        self.locks[media_group_id] = True
        return True

    async def release_lock(self, media_group_id: str) -> None:
        self.locks.pop(media_group_id, None)

    async def get_group(self, media_group_id: str) -> list[Message]:
        return self.groups.get(media_group_id, [])

    async def delete_group(self, media_group_id: str) -> None:
        self.groups.pop(media_group_id, None)
        self.last_message_timers.pop(media_group_id, None)

    async def get_last_message_time(self, media_group_id: str) -> float | None:
        return self.last_message_timers.get(media_group_id)


class MediaGroupAggregatorMiddleware(BaseMiddleware):
    def __init__(
        self,
        media_group_aggregator: BaseMediaGroupAggregator | None = None,
        delay: float = DELAY_SEC,
    ) -> None:
        self.media_group_aggregator = media_group_aggregator or MemoryMediaGroupAggregator()
        self.delay = delay

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.media_group_id:
            return await handler(event, data)
        await self.media_group_aggregator.add_into_group(event.media_group_id, event)
        if not await self.media_group_aggregator.acquire_lock(event.media_group_id):
            return None
        try:
            last_message_time = time.time()
            while True:
                delta = self.delay - (time.time() - last_message_time)
                if delta <= 0:
                    album = await self.media_group_aggregator.get_group(event.media_group_id)
                    if not album:
                        return None
                    album.sort(key=lambda msg: msg.message_id)
                    data.update(album=album)
                    result = await handler(album[0], data)
                    await self.media_group_aggregator.delete_group(event.media_group_id)
                    return result
                await asyncio.sleep(delta)
                new_last_message_time = await self.media_group_aggregator.get_last_message_time(
                    event.media_group_id
                )
                if not new_last_message_time:
                    return None
                last_message_time = new_last_message_time
        finally:
            await self.media_group_aggregator.release_lock(event.media_group_id)
