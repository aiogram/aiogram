import asyncio
import time
from datetime import datetime
from typing import Any, Awaitable, Callable
from unittest import mock

import pytest
from redis.asyncio.client import Redis

from aiogram.dispatcher.middlewares.media_group import (
    BaseMediaGroupAggregator,
    MediaGroupAggregatorMiddleware,
    MemoryMediaGroupAggregator,
    RedisMediaGroupAggregator,
)
from aiogram.types import Chat, Message


def _get_message(message_id: int, **kwargs):
    chat = Chat(id=1, type="private", title="Test")
    return Message(message_id=message_id, date=datetime.now(), chat=chat, **kwargs)


async def wait_until_func_call_sleep(func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
    start_sleep = asyncio.Event()
    real_sleep = asyncio.sleep

    async def mock_sleep(*args, **kwargs):
        start_sleep.set()
        await real_sleep(0)

    with mock.patch("asyncio.sleep", mock_sleep):
        task1 = func(*args, **kwargs)
        await start_sleep.wait()
    return task1


class TestMediaGroupAggregatorMiddleware:
    def get_middleware(self):
        return MediaGroupAggregatorMiddleware(delay=0.1)

    async def test_skip_non_media_group(self):
        is_called = False

        async def next_handler(*args, **kwargs):
            nonlocal is_called
            is_called = True

        await self.get_middleware()(next_handler, _get_message(1), {})
        assert is_called

    async def test_called_once_for_album(self):
        middleware = self.get_middleware()
        counter = 0
        album = None

        async def next_handler(_, data: dict[str, Any]):
            nonlocal counter, album
            counter += 1
            album = data.get("album")

        await asyncio.gather(
            middleware(next_handler, _get_message(1, media_group_id="42"), {}),
            middleware(next_handler, _get_message(2, media_group_id="42"), {}),
        )
        assert album is not None
        assert len(album) == 2
        assert counter == 1

    async def test_bot_object_saved(self, bot):
        middleware = self.get_middleware()
        event = album = None

        async def next_handler(message: Message, data: dict[str, Any]):
            nonlocal event, album
            event = message
            album = data.get("album")

        await middleware(next_handler, _get_message(1, media_group_id="42"), {"bot": bot})
        assert event.bot is bot
        assert all(msg.bot is bot for msg in album)

    async def test_propagate_first_media_in_album(self):
        middleware = self.get_middleware()
        first_message = None

        async def next_handler(message: Message, _):
            nonlocal first_message
            first_message = message

        task1 = await wait_until_func_call_sleep(
            asyncio.create_task, middleware(next_handler, _get_message(2, media_group_id="42"), {})
        )
        await middleware(next_handler, _get_message(1, media_group_id="42"), {})
        await task1
        assert isinstance(first_message, Message)
        assert first_message.message_id == 1

    @pytest.mark.parametrize("deleted_object", ["album", "last_message_time"])
    async def test_skip_propagating_if_data_deleted(self, deleted_object):
        middleware = self.get_middleware()
        counter = 0

        async def next_handler(*args, **kwargs):
            nonlocal counter
            counter += 1

        task1 = await wait_until_func_call_sleep(
            asyncio.create_task, middleware(next_handler, _get_message(1, media_group_id="42"), {})
        )
        if deleted_object == "album":
            middleware.media_group_aggregator.groups.pop("42")
        else:
            middleware.media_group_aggregator.last_message_timers.pop("42")
        await task1
        assert counter == 0

    async def test_different_albums_non_interfere(self):
        middleware = self.get_middleware()
        counter = 0
        albums = []

        async def next_handler(_, data: dict[str, Any]):
            nonlocal counter, albums
            counter += 1
            albums.append(data.get("album"))

        await asyncio.gather(
            middleware(next_handler, _get_message(1, media_group_id="1"), {}),
            middleware(next_handler, _get_message(2, media_group_id="2"), {}),
        )
        assert counter == 2
        assert len(albums) == 2

    async def test_retry_handling(self):
        middleware = self.get_middleware()
        album = None

        async def failed_handler(*args, **kwargs):
            raise RuntimeError("Failed")

        async def working_handler(_, data: dict[str, Any]):
            nonlocal album
            album = data.get("album")

        first_message = _get_message(1, media_group_id="42")
        second_message = _get_message(2, media_group_id="42")
        with pytest.raises(RuntimeError):
            await asyncio.gather(
                middleware(failed_handler, first_message, {}),
                middleware(failed_handler, second_message, {}),
            )
        await middleware(working_handler, first_message, {})
        assert len(album) == 2


def test_message_deduplication():
    message_1, message_2 = _get_message(1), _get_message(2)
    res = [message_1, message_2]
    assert BaseMediaGroupAggregator.deduplicate_messages([message_1, message_2]) == res
    assert BaseMediaGroupAggregator.deduplicate_messages([message_1, message_2, message_2]) == res
    assert BaseMediaGroupAggregator.deduplicate_messages([message_1, message_2, message_1]) == res


@pytest.fixture(params=["memory", "redis"], scope="function")
async def aggregator(request):
    if request.param == "memory":
        yield MemoryMediaGroupAggregator()
    else:
        redis = Redis.from_url(request.getfixturevalue("redis_server"))
        yield RedisMediaGroupAggregator(redis)
        keys = await redis.keys("media_group:*")
        if keys:
            await redis.delete(*keys)
        await redis.aclose()


class TestMediaGroupAggregator:
    async def test_group_creating(self, aggregator: BaseMediaGroupAggregator):
        msg1 = _get_message(1)
        msg2 = _get_message(2)
        assert await aggregator.add_into_group("42", msg1) == 1
        assert await aggregator.add_into_group("42", msg2) == 2
        assert {msg.message_id for msg in await aggregator.get_group("42")} == {
            msg1.message_id,
            msg2.message_id,
        }
        await aggregator.delete_group("42")
        assert await aggregator.get_group("42") == []

    async def test_acquire_lock(self, aggregator: BaseMediaGroupAggregator):
        for _ in range(2):
            assert await aggregator.acquire_lock("42")
            assert not await aggregator.acquire_lock("42")
            await aggregator.release_lock("42")

    async def test_expired_objects_removed(self):
        aggregator = MemoryMediaGroupAggregator()
        await aggregator.add_into_group("42", _get_message(1))
        with mock.patch("time.time", return_value=time.time() + aggregator.ttl_sec + 1):
            new_msg = _get_message(2)
            await aggregator.add_into_group("24", new_msg)
        assert await aggregator.get_group("42") == []
        assert await aggregator.get_group("24") == [new_msg]

    async def test_get_current_time_memory_aggregator(self):
        aggregator = MemoryMediaGroupAggregator()
        with mock.patch("time.time", return_value=1.1):
            assert await aggregator.get_current_time() == 1.1

    async def test_get_current_time_redis_aggregator(self):
        aggregator = RedisMediaGroupAggregator(mock.Mock(spec=Redis))
        aggregator.redis.time = mock.AsyncMock(return_value=(1, 123456))
        assert await aggregator.get_current_time() == 1.123456

    async def test_last_message_time(self, aggregator: BaseMediaGroupAggregator):
        assert await aggregator.get_last_message_time("42") is None
        await aggregator.add_into_group("42", _get_message(1))
        time_before_second_message = time.time()
        assert await aggregator.get_last_message_time("42") <= time_before_second_message
        await aggregator.add_into_group("42", _get_message(2))
        assert await aggregator.get_last_message_time("42") >= time_before_second_message
