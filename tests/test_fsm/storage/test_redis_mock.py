from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage

STORAGE_KEY = StorageKey(bot_id=1, chat_id=1, user_id=1)


class TestRedisStorageMock:
    def test_from_url(self):
        with patch("redis.asyncio.connection.ConnectionPool.from_url") as mock_pool:
            storage = RedisStorage.from_url("redis://localhost:6379/0")
            assert isinstance(storage, RedisStorage)
            mock_pool.assert_called_once_with("redis://localhost:6379/0")

    async def test_close(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        await storage.close()
        redis_mock.aclose.assert_called_once_with(close_connection_pool=True)

    async def test_set_state_none(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        await storage.set_state(key=STORAGE_KEY, state=None)
        redis_mock.delete.assert_called_once()

    async def test_set_state_string(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        await storage.set_state(key=STORAGE_KEY, state="test_state")
        redis_mock.set.assert_called_once()

    async def test_set_state_state_object(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        await storage.set_state(key=STORAGE_KEY, state=State(state="my_state"))
        redis_mock.set.assert_called_once()

    async def test_get_state_bytes(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = b"test_state"
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_state(key=STORAGE_KEY)
        assert result == "test_state"

    async def test_get_state_str(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = "test_state"
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_state(key=STORAGE_KEY)
        assert result == "test_state"

    async def test_get_state_none(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_state(key=STORAGE_KEY)
        assert result is None

    async def test_set_data_invalid(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        with pytest.raises(DataNotDictLikeError):
            await storage.set_data(key=STORAGE_KEY, data=())  # type: ignore[arg-type]

    async def test_set_data_empty(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        await storage.set_data(key=STORAGE_KEY, data={})
        redis_mock.delete.assert_called_once()

    async def test_set_data_non_empty(self):
        redis_mock = AsyncMock()
        storage = RedisStorage(redis=redis_mock)
        await storage.set_data(key=STORAGE_KEY, data={"foo": "bar"})
        redis_mock.set.assert_called_once()

    async def test_get_data_none(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_data(key=STORAGE_KEY)
        assert result == {}

    async def test_get_data_bytes(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = b'{"foo": "bar"}'
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_data(key=STORAGE_KEY)
        assert result == {"foo": "bar"}

    async def test_get_data_str(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = '{"foo": "bar"}'
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_data(key=STORAGE_KEY)
        assert result == {"foo": "bar"}

    async def test_get_value_uses_base_implementation(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = b'{"foo": "bar"}'
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_value(storage_key=STORAGE_KEY, dict_key="foo")
        assert result == "bar"

    async def test_get_value_default(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None
        storage = RedisStorage(redis=redis_mock)
        result = await storage.get_value(storage_key=STORAGE_KEY, dict_key="missing", default="x")
        assert result == "x"


class TestRedisEventIsolationLockMock:
    async def test_lock(self):
        redis_mock = MagicMock()
        lock_cm = AsyncMock()
        redis_mock.lock.return_value = lock_cm

        isolation = RedisEventIsolation(redis=redis_mock)
        async with isolation.lock(key=STORAGE_KEY):
            pass

        redis_mock.lock.assert_called_once()
