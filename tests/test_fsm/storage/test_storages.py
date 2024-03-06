import pytest

from aiogram.fsm.storage.base import BaseStorage, StorageKey
from tests.mocked_bot import MockedBot


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)


@pytest.mark.parametrize(
    "storage",
    [pytest.lazy_fixture("redis_storage"), pytest.lazy_fixture("memory_storage")],
)
class TestStorages:
    async def test_set_state(self, bot: MockedBot, storage: BaseStorage, storage_key: StorageKey):
        assert await storage.get_state(key=storage_key) is None

        await storage.set_state(key=storage_key, state="state")
        assert await storage.get_state(key=storage_key) == "state"
        await storage.set_state(key=storage_key, state=None)
        assert await storage.get_state(key=storage_key) is None

    async def test_set_data(self, bot: MockedBot, storage: BaseStorage, storage_key: StorageKey):
        assert await storage.get_data(key=storage_key) == {}

        await storage.set_data(key=storage_key, data={"foo": "bar"})
        assert await storage.get_data(key=storage_key) == {"foo": "bar"}
        await storage.set_data(key=storage_key, data={})
        assert await storage.get_data(key=storage_key) == {}

    async def test_update_data(
        self, bot: MockedBot, storage: BaseStorage, storage_key: StorageKey
    ):
        assert await storage.get_data(key=storage_key) == {}
        assert await storage.update_data(key=storage_key, data={"foo": "bar"}) == {"foo": "bar"}
        assert await storage.update_data(key=storage_key, data={"baz": "spam"}) == {
            "foo": "bar",
            "baz": "spam",
        }
        assert await storage.get_data(key=storage_key) == {
            "foo": "bar",
            "baz": "spam",
        }

    async def test_get_value(self, bot: MockedBot, storage: BaseStorage, storage_key: StorageKey):
        await storage.set_data(key=storage_key, data={"hello": "world"})
        assert await storage.get_value(key=storage_key, data_key="hello") == "world"
        assert await storage.get_value(key=storage_key, data_key="12345") is None
        assert await storage.get_value(key=storage_key, data_key="qwerty", default=42) == 42
