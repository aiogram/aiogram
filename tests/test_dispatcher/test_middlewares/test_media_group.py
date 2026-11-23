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
from aiogram.dispatcher.middlewares.user_context import EventContext
from aiogram.types import Message, Update
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import SimpleEventIsolation, StorageKey
from dataclasses import replace

from aiogram.types.chat import Chat


def _get_raw_message(message_id: int, **kwargs):
    return {
        "message_id": message_id,
        "date": datetime.now().timestamp(),
        "chat": {"id": 1, "type": "private", "title": "Test"},
        **kwargs,
    }


def _get_message(message_id: int, context: dict[str, Any] | None = None, **kwargs):
    return Message.model_validate(_get_raw_message(message_id, **kwargs), context=context)


def _get_update(message_id: int, context: dict[str, Any] | None = None, **kwargs):
    return Update.model_validate(
        {"update_id": 42, "message": _get_raw_message(message_id, **kwargs)}, context=context
    )


async def wait_until_func_call_sleep(
    func: Callable[..., Awaitable[Any]], *args, timeout: float = 0.2, **kwargs
) -> Any:
    start_sleep = asyncio.Event()
    real_sleep = asyncio.sleep

    async def mock_sleep(*_, **__):
        start_sleep.set()
        await real_sleep(0)

    with mock.patch("asyncio.sleep", mock_sleep):
        task1 = func(*args, **kwargs)
        await asyncio.wait_for(start_sleep.wait(), timeout=timeout)
    return task1


async def capture_first_event(
    middleware: MediaGroupAggregatorMiddleware,
    *updates: list[Update],
    context: dict[str, Any] = {},
) -> Update:
    captured_update = None

    async def next_handler(event, _):
        nonlocal captured_update
        captured_update = event

    tasks = []
    for update in updates:
        task = await wait_until_func_call_sleep(
            asyncio.create_task, middleware(next_handler, update, context)
        )
        tasks.append(task)
    await asyncio.gather(*tasks)
    return captured_update


def get_key(group_id: str) -> StorageKey:
    return StorageKey(
        bot_id=1,
        chat_id=1,
        user_id=1,
        thread_id=None,
        business_connection_id=None,
        destiny=group_id,
    )


class TestMediaGroupAggregatorMiddleware:
    def get_middleware(self, mock_key_builder: bool = True, **kwargs):
        kwargs.setdefault("delay", 0.1)
        middleware = MediaGroupAggregatorMiddleware(**kwargs)
        if mock_key_builder:
            middleware.build_key = lambda _, __, media_group_id: get_key(media_group_id)
        return middleware

    async def test_raise_exception_if_wrong_event_type(self):
        async def next_handler(*_, **__):
            pass

        with pytest.raises(RuntimeError):
            await self.get_middleware()(next_handler, _get_message(1), {})

    async def test_skip_non_media_group(self):
        is_called = False

        async def next_handler(*_, **__):
            nonlocal is_called
            is_called = True

        await self.get_middleware()(next_handler, _get_update(1), {})
        assert is_called

    async def test_build_key_if_user_is_none(self, bot):
        middleware = self.get_middleware()
        event_context = EventContext(chat=Chat(id=1, type="private"))
        key = middleware.build_key(bot, event_context, "42")
        assert key == StorageKey(
            bot_id=1,
            chat_id=1,
            user_id=1,
            thread_id=None,
            business_connection_id=None,
            destiny="42",
        )

    async def test_called_once_for_album(self):
        middleware = self.get_middleware()
        counter = 0
        album = None

        async def next_handler(_, data: dict[str, Any]):
            nonlocal counter, album
            counter += 1
            album = data.get("album")

        await asyncio.gather(
            middleware(next_handler, _get_update(1, media_group_id="42"), {}),
            middleware(next_handler, _get_update(2, media_group_id="42"), {}),
        )
        assert album is not None
        assert len(album) == 2
        assert counter == 1

    async def test_bot_object_saved(self, bot, aggregator: BaseMediaGroupAggregator):
        CONTEXT = {"bot": bot}
        nested_object = _get_raw_message(2)
        update = await capture_first_event(
            self.get_middleware(media_group_aggregator=aggregator),
            _get_update(1, reply_to_message=nested_object, media_group_id="42", context=CONTEXT),
            context=CONTEXT,
        )
        assert isinstance(update, Update)
        assert update.event.bot is bot
        assert update.event.reply_to_message.bot is bot

    @pytest.mark.parametrize("event_type", ["message", "channel_post"])
    async def test_keep_original_event_type(self, event_type):
        update = await capture_first_event(
            self.get_middleware(),
            Update(
                update_id=1,
                **{event_type: _get_raw_message(1, media_group_id="42")},
            ),
        )
        assert isinstance(update, Update)
        assert update.event_type == event_type

    async def test_propagate_first_media_in_album(self):
        update = await capture_first_event(
            self.get_middleware(),
            _get_update(2, media_group_id="42"),
            _get_update(1, media_group_id="42"),
        )
        assert update.event.message_id == 1

    async def test_aggregation_with_event_isolation(self, bot):
        dp = Dispatcher(
            events_isolation=SimpleEventIsolation(),
            media_group_aggregator=self.get_middleware(mock_key_builder=False),
        )
        counter = 0

        async def handler(_):
            nonlocal counter
            counter += 1

        dp.message.register(handler)
        await asyncio.gather(
            dp.feed_update(bot, _get_update(1, media_group_id="42")),
            dp.feed_update(bot, _get_update(2, media_group_id="42")),
        )
        assert counter == 1

    @pytest.mark.parametrize("deleted_object", ["album", "last_message_time"])
    async def test_skip_propagating_if_data_deleted(self, deleted_object):
        middleware = self.get_middleware()
        counter = 0

        async def next_handler(*_, **__):
            nonlocal counter
            counter += 1

        task1 = await wait_until_func_call_sleep(
            asyncio.create_task, middleware(next_handler, _get_update(1, media_group_id="42"), {})
        )
        if deleted_object == "album":
            middleware.media_group_aggregator.groups.pop(get_key("42"))
        else:
            middleware.media_group_aggregator.last_message_timers.pop(get_key("42"))
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
            middleware(next_handler, _get_update(1, media_group_id="1"), {}),
            middleware(next_handler, _get_update(2, media_group_id="2"), {}),
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

        first_message = _get_update(1, media_group_id="42")
        second_message = _get_update(2, media_group_id="42")
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
    @pytest.fixture
    def key(self):
        return get_key("42")

    async def test_group_creating(self, bot, aggregator: BaseMediaGroupAggregator, key):
        msg1 = _get_message(1)
        msg2 = _get_message(2)
        assert await aggregator.add_into_group(key, msg1) == 1
        assert await aggregator.add_into_group(key, msg2) == 2
        assert {msg.message_id for msg in await aggregator.get_group(key, bot)} == {
            msg1.message_id,
            msg2.message_id,
        }
        await aggregator.delete_group(key)
        assert await aggregator.get_group(key, bot) == []

    async def test_acquire_lock(self, aggregator: BaseMediaGroupAggregator, key):
        for i in ("lock1", "lock2"):
            assert await aggregator.acquire_lock(key, i)
            assert not await aggregator.acquire_lock(key, i)
            await aggregator.release_lock(key, i)

    async def test_lock_not_acquired_with_wrong_key(
        self, aggregator: BaseMediaGroupAggregator, key
    ):
        await aggregator.acquire_lock(key, "key1")
        await aggregator.release_lock(key, "key2")
        assert not await aggregator.acquire_lock(key, "key1")

    async def test_expired_objects_removed(self, bot, key):
        aggregator = MemoryMediaGroupAggregator()
        await aggregator.add_into_group(key, _get_message(1))
        second_key = replace(key, destiny="24")
        with mock.patch("time.monotonic", return_value=time.time() + aggregator.ttl_sec + 1):
            new_msg = _get_message(2)
            await aggregator.add_into_group(second_key, new_msg)
        assert await aggregator.get_group(key, bot) == []
        assert await aggregator.get_group(second_key, bot) == [new_msg]

    async def test_get_current_time_memory_aggregator(self):
        aggregator = MemoryMediaGroupAggregator()
        with mock.patch("time.monotonic", return_value=1.1):
            assert await aggregator.get_current_time() == 1.1

    async def test_get_current_time_redis_aggregator(self):
        aggregator = RedisMediaGroupAggregator(mock.Mock(spec=Redis))
        aggregator.redis.time = mock.AsyncMock(return_value=(1, 123456))
        assert await aggregator.get_current_time() == 1.123456

    async def test_last_message_time(self, aggregator: BaseMediaGroupAggregator, key):
        assert await aggregator.get_last_message_time(key) is None
        await aggregator.add_into_group(key, _get_message(1))
        time_before_second_message = await aggregator.get_current_time()
        assert await aggregator.get_last_message_time(key) <= time_before_second_message
        await aggregator.add_into_group(key, _get_message(2))
        assert await aggregator.get_last_message_time(key) >= time_before_second_message
