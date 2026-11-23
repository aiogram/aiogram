from typing import TypedDict

import pytest

from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import (
    UNCHANGED,
    BaseStorage,
    StorageKey,
    StorageRecord,
    StorageWrite,
)
from aiogram.fsm.storage.memory import MemoryStorage
from tests.conftest import MinimalStorage


def other_key(key: StorageKey) -> StorageKey:
    return StorageKey(bot_id=key.bot_id, chat_id=key.chat_id + 1, user_id=key.user_id + 1)


async def batch_scenario(storage: BaseStorage, key: StorageKey) -> list[StorageRecord]:
    """Writes over two keys, partly UNCHANGED and partly cleared, then a read of both."""
    key2 = other_key(key)
    await storage.apply_writes(
        StorageWrite(key, state="a", data={"x": 1}),
        StorageWrite(key2, data={"y": 2}),
        StorageWrite(key, state=State("b", group_name="G")),
        StorageWrite(key2, state="c", data={}),
    )
    return await storage.get_records(key, key2, key)


@pytest.mark.parametrize(
    "storage",
    ["memory_storage", "minimal_storage", "redis_storage", "mongo_storage", "pymongo_storage"],
    indirect=True,
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

    async def test_get_records(self, storage: BaseStorage, storage_key: StorageKey):
        key2 = other_key(storage_key)
        assert await storage.get_records() == []
        assert await storage.get_records(storage_key, key2) == [StorageRecord(), StorageRecord()]

        await storage.set_state(key=storage_key, state="state")
        await storage.set_data(key=key2, data={"foo": "bar"})
        records = await storage.get_records(key2, storage_key, key2)
        assert records == [
            StorageRecord(data={"foo": "bar"}),
            StorageRecord(state="state"),
            StorageRecord(data={"foo": "bar"}),
        ]

        records[0].data["foo"] = "changed"  # the caller owns the copy
        assert await storage.get_data(key=key2) == {"foo": "bar"}

    async def test_apply_writes(self, storage: BaseStorage, storage_key: StorageKey):
        key2 = other_key(storage_key)
        await storage.apply_writes()
        assert await batch_scenario(storage, storage_key) == [
            StorageRecord(state="G:b", data={"x": 1}),
            StorageRecord(state="c"),
            StorageRecord(state="G:b", data={"x": 1}),
        ]

        await storage.apply_writes(StorageWrite(storage_key))  # all UNCHANGED: nothing changes
        assert await storage.get_records(storage_key) == [
            StorageRecord(state="G:b", data={"x": 1})
        ]

        await storage.apply_writes(StorageWrite(storage_key, state=None, data={}))
        await storage.apply_writes(StorageWrite(key2, state=None))
        assert await storage.get_records(storage_key, key2) == [StorageRecord(), StorageRecord()]

    async def test_apply_writes_copies_data(self, storage: BaseStorage, storage_key: StorageKey):
        data = {"foo": "bar"}
        await storage.apply_writes(StorageWrite(storage_key, data=data))
        data["foo"] = "changed"
        assert await storage.get_data(key=storage_key) == {"foo": "bar"}

    async def test_apply_writes_not_dict(self, storage: BaseStorage, storage_key: StorageKey):
        with pytest.raises(DataNotDictLikeError):
            await storage.apply_writes(StorageWrite(storage_key, data=()))


async def test_fallback_matches_memory(storage_key: StorageKey):
    assert await batch_scenario(MinimalStorage(), storage_key) == await batch_scenario(
        MemoryStorage(), storage_key
    )


def test_unchanged_repr():
    assert repr(UNCHANGED) == "UNCHANGED"
    assert StorageWrite(StorageKey(bot_id=1, chat_id=1, user_id=1)).state is UNCHANGED


def test_record_is_keyword_only():
    with pytest.raises(TypeError):
        StorageRecord("state", {})  # type: ignore[misc]


async def test_fallback_record_data_is_a_copy(storage_key: StorageKey):
    class AliasingStorage(MinimalStorage):
        async def get_data(self, key: StorageKey) -> dict:
            return self.datas.setdefault(key, {})  # the internal dict itself

    storage = AliasingStorage()
    await storage.set_data(storage_key, {"foo": "bar"})
    (record,) = await storage.get_records(storage_key)
    record.data["foo"] = "changed"
    assert storage.datas[storage_key] == {"foo": "bar"}
