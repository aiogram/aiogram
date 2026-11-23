import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, cast

from aiogram import Bot
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.fsm.storage.base import DefaultKeyBuilder, KeyBuilder, StorageKey
from aiogram.types import Message, TelegramObject, Update

if TYPE_CHECKING:
    from redis.asyncio.client import Redis

DELAY_SEC = 1.0
LOCK_TTL_SEC = 30
TTL_SEC = 600


class BaseMediaGroupAggregator(ABC):
    @abstractmethod
    async def add_into_group(self, key: StorageKey, media: Message) -> int:
        pass

    @abstractmethod
    async def acquire_lock(self, key: StorageKey, lock_id: str) -> bool:
        pass

    @abstractmethod
    async def release_lock(self, key: StorageKey, lock_id: str) -> None:
        pass

    @abstractmethod
    async def get_group(self, key: StorageKey, bot: Bot) -> list[Message]:
        pass

    @abstractmethod
    async def delete_group(self, key: StorageKey) -> None:
        pass

    @abstractmethod
    async def get_last_message_time(self, key: StorageKey) -> float | None:
        pass

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

    @abstractmethod
    async def get_current_time(self) -> float:
        pass


class RedisMediaGroupAggregator(BaseMediaGroupAggregator):
    """
    Aggregates media groups in Redis.
    """

    redis: "Redis"

    def __init__(
        self,
        redis: "Redis",
        ttl_sec: int = TTL_SEC,
        lock_ttl_sec: int = LOCK_TTL_SEC,
        key_builder: KeyBuilder | None = None,
    ) -> None:
        """
        :param ttl_sec: ttl for media group data in seconds
        :param lock_ttl_sec: ttl for lock in seconds. Value should be large enough to prevent the
            lock from expiring before the handler finishes, but small enough to expire before
            Telegram retries a failed delivery.
        """
        self.redis = redis
        self.ttl_sec = ttl_sec
        self.lock_ttl_sec = lock_ttl_sec
        self.key_builder = key_builder or DefaultKeyBuilder(
            prefix="media_group", with_destiny=True
        )

    def build_group_key(self, key: StorageKey) -> str:
        return self.key_builder.build(key, "data")

    def build_last_message_time_key(self, key: StorageKey) -> str:
        return self.key_builder.build(key)

    def build_group_lock_key(self, key: StorageKey) -> str:
        return self.key_builder.build(key, "lock")

    async def add_into_group(self, key: StorageKey, media: Message) -> int:
        current_time = await self.get_current_time()
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(self.build_last_message_time_key(key), current_time, ex=self.ttl_sec)
            pipe.rpush(self.build_group_key(key), media.model_dump_json())
            pipe.expire(self.build_group_key(key), self.ttl_sec)
            res = await pipe.execute()
        return cast(int, res[1])

    async def acquire_lock(self, key: StorageKey, lock_id: str) -> bool:
        return cast(
            bool,
            await self.redis.set(
                self.build_group_lock_key(key), lock_id, nx=True, ex=self.lock_ttl_sec
            ),
        )

    async def release_lock(self, key: StorageKey, lock_id: str) -> None:
        release_script = (
            'if redis.call("get", KEYS[1]) == ARGV[1] then '
            'return redis.call("del", KEYS[1]) '
            "else return 0 end"
        )
        await cast(
            Awaitable[int],
            self.redis.eval(release_script, 1, self.build_group_lock_key(key), lock_id),
        )

    async def get_group(self, key: StorageKey, bot: Bot) -> list[Message]:
        result = await cast(
            Awaitable[list[str]], self.redis.lrange(self.build_group_key(key), 0, -1)
        )
        return self.deduplicate_messages(
            [Message.model_validate_json(msg, context={"bot": bot}) for msg in result]
        )

    async def delete_group(self, key: StorageKey) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.delete(self.build_group_key(key))
            pipe.delete(self.build_last_message_time_key(key))
            await pipe.execute()

    async def get_last_message_time(self, key: StorageKey) -> float | None:
        result = await self.redis.get(self.build_last_message_time_key(key))
        if result is None:
            return None
        return float(result)

    async def get_current_time(self) -> float:
        seconds, microseconds = cast(tuple[int, int], await self.redis.time())
        return seconds + microseconds / 1e6


class MemoryMediaGroupAggregator(BaseMediaGroupAggregator):
    def __init__(self, ttl_sec: int = TTL_SEC) -> None:
        self.groups: dict[StorageKey, list[Message]] = defaultdict(list)
        self.last_message_timers: dict[StorageKey, float] = {}
        self.locks: dict[StorageKey, str] = {}
        self.ttl_sec = ttl_sec

    def remove_expired_objects(self) -> None:
        expired_group_ids = []
        current_time = time.monotonic()
        for group_id, last_message_time in self.last_message_timers.items():
            if current_time - last_message_time > self.ttl_sec:
                expired_group_ids.append(group_id)
            else:
                break  # the list is sorted in ascending order
                # because python 3.7+ save dict in insertion order
        for group_id in expired_group_ids:
            self.groups.pop(group_id, None)
            self.last_message_timers.pop(group_id, None)
            self.locks.pop(group_id, None)

    async def add_into_group(self, key: StorageKey, media: Message) -> int:
        self.remove_expired_objects()
        if media.message_id not in (msg.message_id for msg in self.groups[key]):
            self.groups[key].append(media)
        self.last_message_timers.pop(key, None)
        self.last_message_timers[key] = time.monotonic()
        return len(self.groups[key])

    async def acquire_lock(self, key: StorageKey, lock_id: str) -> bool:
        if self.locks.get(key) is not None:
            return False
        self.locks[key] = lock_id
        return True

    async def release_lock(self, key: StorageKey, lock_id: str) -> None:
        if self.locks.get(key) == lock_id:
            self.locks.pop(key)

    async def get_group(self, key: StorageKey, bot: Bot) -> list[Message]:
        return self.groups.get(key, [])

    async def delete_group(self, key: StorageKey) -> None:
        self.groups.pop(key, None)
        self.last_message_timers.pop(key, None)

    async def get_last_message_time(self, key: StorageKey) -> float | None:
        return self.last_message_timers.get(key)

    async def get_current_time(self) -> float:
        return time.monotonic()


class MediaGroupAggregatorMiddleware(BaseMiddleware):
    def __init__(
        self,
        media_group_aggregator: BaseMediaGroupAggregator | None = None,
        delay: float = DELAY_SEC,
    ) -> None:
        """
        :param delay: delay between last received message in media group and processing it
        """
        self.media_group_aggregator = media_group_aggregator or MemoryMediaGroupAggregator()
        self.delay = delay

    def build_key(self, bot: Bot, event_context: EventContext, media_group_id: str) -> StorageKey:
        chat_id = cast(int, event_context.chat_id)
        return StorageKey(
            bot_id=bot.id,
            chat_id=chat_id,
            user_id=event_context.user_id or chat_id,
            thread_id=event_context.thread_id,
            business_connection_id=event_context.business_connection_id,
            destiny=media_group_id,
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            raise RuntimeError("MediaGroupAggregatorMiddleware got an unexpected event type!")
        message = event.event
        if not isinstance(message, Message) or not message.media_group_id:
            return await handler(event, data)
        bot = cast(Bot, data.get("bot"))
        key = self.build_key(
            bot, cast(EventContext, data.get(EVENT_CONTEXT_KEY)), message.media_group_id
        )
        await self.media_group_aggregator.add_into_group(key, message)
        lock_id = str(uuid.uuid4())
        if not await self.media_group_aggregator.acquire_lock(key, lock_id):
            return None
        try:
            while True:
                last_message_time = await self.media_group_aggregator.get_last_message_time(key)
                if not last_message_time:
                    return None
                delta = self.delay - (
                    await self.media_group_aggregator.get_current_time() - last_message_time
                )
                if delta <= 0:
                    album = await self.media_group_aggregator.get_group(key, bot)
                    if not album:
                        return None
                    album.sort(key=lambda msg: msg.message_id)
                    data.update(album=album)
                    result = await handler(
                        event.model_copy(update={event.event_type: album[0]}), data
                    )
                    await self.media_group_aggregator.delete_group(key)
                    return result
                await asyncio.sleep(delta)
        finally:
            await self.media_group_aggregator.release_lock(key, lock_id)
