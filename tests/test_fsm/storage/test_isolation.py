import asyncio
from random import randint, uniform

import pytest

from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import DisabledEventIsolation, SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisEventIsolation
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)


@pytest.mark.parametrize("isolation", [pytest.lazy_fixture("disabled_isolation")])
class TestDisabledIsolation:
    async def test_lock(
        self,
        bot: MockedBot,
        isolation: DisabledEventIsolation,
        storage_key: StorageKey,
    ):
        async with isolation.lock(bot=bot, key=storage_key):
            assert True, "You are kidding me?"


@pytest.mark.parametrize("isolation", [pytest.lazy_fixture("lock_isolation")])
class TestLockIsolations:
    @staticmethod
    async def _some_task(isolation: SimpleEventIsolation, bot: MockedBot, key: StorageKey):
        async with isolation.lock(bot=bot, key=key):
            await asyncio.sleep(uniform(0, 1))

    @staticmethod
    def random_storage_key(bot: MockedBot):
        return StorageKey(chat_id=randint(-44, -40), user_id=randint(40, 44), bot_id=bot.id)

    async def test_lock(
        self,
        bot: MockedBot,
        isolation: SimpleEventIsolation,
    ):
        tasks = []

        for _ in range(100):
            tasks.append(
                asyncio.create_task(self._some_task(isolation, bot, self.random_storage_key(bot)))
            )
            await asyncio.sleep(0.01)

        await asyncio.gather(*[task for task in tasks if not task.done()])
        assert len(isolation._locks) == 0


@pytest.mark.parametrize("isolation", [pytest.lazy_fixture("redis_isolation")])
class TestRedisIsolation:
    async def test_lock(
        self,
        bot: MockedBot,
        isolation: RedisEventIsolation,
        storage_key: StorageKey,
    ):
        async with isolation.lock(bot=bot, key=storage_key):
            assert True, "You are kidding me?"
