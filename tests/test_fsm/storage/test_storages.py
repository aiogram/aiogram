import pytest
from pytest_lazy_fixtures import lf

from aiogram.fsm.storage.base import BaseStorage, StorageKey


@pytest.mark.parametrize(
    "storage",
    [
        lf("redis_storage"),
        lf("mongo_storage"),
        lf("memory_storage"),
    ],
)
class TestStorages:
    async def test_set_state(self, storage: BaseStorage, storage_key: StorageKey):
        assert await storage.get_state(key=storage_key) is None

        await storage.set_state(key=storage_key, state="state")
        assert await storage.get_state(key=storage_key) == "state"
        await storage.set_state(key=storage_key, state=None)
        assert await storage.get_state(key=storage_key) is None

    async def test_set_data(self, storage: BaseStorage, storage_key: StorageKey):
        assert await storage.get_data(key=storage_key) == {}

        await storage.set_data(key=storage_key, data={"foo": "bar"})
        assert await storage.get_data(key=storage_key) == {"foo": "bar"}
        await storage.set_data(key=storage_key, data={})
        assert await storage.get_data(key=storage_key) == {}

    async def test_update_data(self, storage: BaseStorage, storage_key: StorageKey):
        assert await storage.get_data(key=storage_key) == {}
        assert await storage.update_data(key=storage_key, data={"foo": "bar"}) == {"foo": "bar"}
        assert await storage.update_data(key=storage_key, data={}) == {"foo": "bar"}
        assert await storage.get_data(key=storage_key) == {"foo": "bar"}
        assert await storage.update_data(key=storage_key, data={"baz": "spam"}) == {
            "foo": "bar",
            "baz": "spam",
        }
        assert await storage.get_data(key=storage_key) == {
            "foo": "bar",
            "baz": "spam",
        }
        assert await storage.update_data(key=storage_key, data={"baz": "test"}) == {
            "foo": "bar",
            "baz": "test",
        }
        assert await storage.get_data(key=storage_key) == {
            "foo": "bar",
            "baz": "test",
        }
