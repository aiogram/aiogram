from unittest import mock
from unittest.mock import AsyncMock, patch

import pytest

from aiogram.fsm.storage.base import BaseEventIsolation, StorageKey
from aiogram.fsm.storage.redis import RedisEventIsolation
from tests.mocked_bot import MockedBot


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)


@pytest.mark.parametrize(
    "isolation",
    [
        pytest.lazy_fixture("redis_isolation"),
        pytest.lazy_fixture("lock_isolation"),
        pytest.lazy_fixture("disabled_isolation"),
    ],
)
class TestIsolations:
    async def test_lock(
        self,
        isolation: BaseEventIsolation,
        storage_key: StorageKey,
    ):
        async with isolation.lock(key=storage_key):
            assert True, "Are you kidding me?"


class TestRedisEventIsolation:
    def test_init_without_key_builder(self):
        redis = AsyncMock()
        isolation = RedisEventIsolation(redis=redis)
        assert isolation.redis is redis

        assert isolation.key_builder is not None

    def test_init_with_key_builder(self):
        redis = AsyncMock()
        key_builder = AsyncMock()
        isolation = RedisEventIsolation(redis=redis, key_builder=key_builder)
        assert isolation.redis is redis
        assert isolation.key_builder is key_builder

    def test_create_from_url(self):
        with patch("redis.asyncio.connection.ConnectionPool.from_url") as pool:
            isolation = RedisEventIsolation.from_url("redis://localhost:6379/0")
            assert isinstance(isolation, RedisEventIsolation)
            assert isolation.redis is not None
            assert isolation.key_builder is not None

            pool.assert_called_once_with("redis://localhost:6379/0")

    async def test_close(self):
        isolation = RedisEventIsolation(redis=AsyncMock())
        await isolation.close()

        # close is not called because connection should be closed from the storage
        # assert isolation.redis.close.called_once()
