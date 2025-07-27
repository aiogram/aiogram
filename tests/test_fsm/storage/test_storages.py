from typing import TypedDict

import pytest

from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.storage.base import BaseStorage, StorageKey


@pytest.mark.parametrize(
    "storage",
    [
        pytest.lazy_fixture("redis_storage"),
        pytest.lazy_fixture("mongo_storage"),
        pytest.lazy_fixture("memory_storage"),
        pytest.lazy_fixture("sqlite_storage"),
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
        assert await storage.get_value(storage_key=storage_key, dict_key="foo") is None
        assert (
            await storage.get_value(storage_key=storage_key, dict_key="foo", default="baz")
            == "baz"
        )

        await storage.set_data(key=storage_key, data={"foo": "bar"})
        assert await storage.get_data(key=storage_key) == {"foo": "bar"}
        assert await storage.get_value(storage_key=storage_key, dict_key="foo") == "bar"
        assert (
            await storage.get_value(storage_key=storage_key, dict_key="foo", default="baz")
            == "bar"
        )

        await storage.set_data(key=storage_key, data={})
        assert await storage.get_data(key=storage_key) == {}
        assert await storage.get_value(storage_key=storage_key, dict_key="foo") is None
        assert (
            await storage.get_value(storage_key=storage_key, dict_key="foo", default="baz")
            == "baz"
        )

        class CustomTypedDict(TypedDict, total=False):
            foo: str
            bar: str

        await storage.set_data(key=storage_key, data=CustomTypedDict(foo="bar", bar="baz"))
        assert await storage.get_data(key=storage_key) == {"foo": "bar", "bar": "baz"}
        assert await storage.get_value(storage_key=storage_key, dict_key="foo") == "bar"
        assert (
            await storage.get_value(storage_key=storage_key, dict_key="foo", default="baz")
            == "bar"
        )

        with pytest.raises(DataNotDictLikeError):
            await storage.set_data(key=storage_key, data=())

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
