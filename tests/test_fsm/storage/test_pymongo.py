import pytest
from pymongo.errors import PyMongoError

from aiogram.fsm.state import State
from aiogram.fsm.storage.pymongo import PyMongoStorage, StorageKey
from tests.conftest import CHAT_ID, USER_ID

PREFIX = "fsm"


async def test_get_storage_passing_only_url(pymongo_server):
    storage = PyMongoStorage.from_url(url=pymongo_server)
    try:
        await storage._client.server_info()
    except PyMongoError as e:
        pytest.fail(str(e))


async def test_pymongo_storage_close_does_not_throw(pymongo_server):
    storage = PyMongoStorage.from_url(url=pymongo_server)
    try:
        assert await storage.close() is None
    except Exception as e:
        pytest.fail(f"close() raised an exception: {e}")


async def test_update_not_existing_data_with_empty_dictionary(
    pymongo_storage: PyMongoStorage,
    storage_key: StorageKey,
):
    assert await pymongo_storage._collection.find_one({}) is None
    assert await pymongo_storage.update_data(key=storage_key, data={}) == {}
    assert await pymongo_storage._collection.find_one({}) is None


async def test_update_not_existing_data_with_non_empty_dictionary(
    pymongo_storage: PyMongoStorage,
    storage_key: StorageKey,
):
    assert await pymongo_storage._collection.find_one({}) is None
    assert await pymongo_storage.update_data(key=storage_key, data={"key": "value"}) == {
        "key": "value"
    }
    assert await pymongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "data": {"key": "value"},
    }
    await pymongo_storage._collection.delete_one({})


async def test_update_existing_data_with_empty_dictionary(
    pymongo_storage: PyMongoStorage,
    storage_key: StorageKey,
):
    assert await pymongo_storage._collection.find_one({}) is None
    await pymongo_storage.set_data(key=storage_key, data={"key": "value"})
    assert await pymongo_storage.update_data(key=storage_key, data={}) == {"key": "value"}
    assert await pymongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "data": {"key": "value"},
    }
    await pymongo_storage._collection.delete_one({})


async def test_update_existing_data_with_non_empty_dictionary(
    pymongo_storage: PyMongoStorage,
    storage_key: StorageKey,
):
    assert await pymongo_storage._collection.find_one({}) is None
    await pymongo_storage.set_data(key=storage_key, data={"key": "value"})
    assert await pymongo_storage.update_data(key=storage_key, data={"key": "new_value"}) == {
        "key": "new_value"
    }
    assert await pymongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "data": {"key": "new_value"},
    }
    await pymongo_storage._collection.delete_one({})


async def test_document_life_cycle(
    pymongo_storage: PyMongoStorage,
    storage_key: StorageKey,
):
    assert await pymongo_storage._collection.find_one({}) is None
    await pymongo_storage.set_state(storage_key, "test")
    await pymongo_storage.set_data(storage_key, {"key": "value"})
    assert await pymongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "state": "test",
        "data": {"key": "value"},
    }
    await pymongo_storage.set_state(storage_key, None)
    assert await pymongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "data": {"key": "value"},
    }
    await pymongo_storage.set_data(storage_key, {})
    assert await pymongo_storage._collection.find_one({}) is None


class TestStateAndDataDoNotAffectEachOther:
    async def test_state_and_data_do_not_affect_each_other_while_getting(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        assert await pymongo_storage._collection.find_one({}) is None
        await pymongo_storage.set_state(storage_key, "test")
        await pymongo_storage.set_data(storage_key, {"key": "value"})
        assert await pymongo_storage.get_state(storage_key) == "test"
        assert await pymongo_storage.get_data(storage_key) == {"key": "value"}

    async def test_data_do_not_affect_to_deleted_state_getting(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        await pymongo_storage.set_state(storage_key, "test")
        await pymongo_storage.set_data(storage_key, {"key": "value"})
        await pymongo_storage.set_state(storage_key, None)
        assert await pymongo_storage.get_state(storage_key) is None

    async def test_state_do_not_affect_to_deleted_data_getting(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        await pymongo_storage.set_state(storage_key, "test")
        await pymongo_storage.set_data(storage_key, {"key": "value"})
        await pymongo_storage.set_data(storage_key, {})
        assert await pymongo_storage.get_data(storage_key) == {}

    async def test_state_do_not_affect_to_updating_not_existing_data_with_empty_dictionary(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        await pymongo_storage.set_state(storage_key, "test")
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test"
        }
        assert await pymongo_storage.update_data(key=storage_key, data={}) == {}
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test"
        }

    async def test_state_do_not_affect_to_updating_not_existing_data_with_non_empty_dictionary(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        await pymongo_storage.set_state(storage_key, "test")
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test"
        }
        assert await pymongo_storage.update_data(
            key=storage_key,
            data={"key": "value"},
        ) == {"key": "value"}
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }

    async def test_state_do_not_affect_to_updating_existing_data_with_empty_dictionary(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        await pymongo_storage.set_state(storage_key, "test")
        await pymongo_storage.set_data(storage_key, {"key": "value"})
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }
        assert await pymongo_storage.update_data(key=storage_key, data={}) == {"key": "value"}
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }

    async def test_state_do_not_affect_to_updating_existing_data_with_non_empty_dictionary(
        self,
        pymongo_storage: PyMongoStorage,
        storage_key: StorageKey,
    ):
        await pymongo_storage.set_state(storage_key, "test")
        await pymongo_storage.set_data(storage_key, {"key": "value"})
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }
        assert await pymongo_storage.update_data(
            key=storage_key,
            data={"key": "VALUE", "key_2": "value_2"},
        ) == {"key": "VALUE", "key_2": "value_2"}
        assert await pymongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "VALUE", "key_2": "value_2"},
        }


@pytest.mark.parametrize(
    "value,result",
    [
        [None, None],
        ["", ""],
        ["text", "text"],
        [State(), None],
        [State(state="*"), "*"],
        [State("text"), "@:text"],
        [State("test", group_name="Test"), "Test:test"],
        [[1, 2, 3], "[1, 2, 3]"],
    ],
)
def test_resolve_state(value, result, pymongo_storage: PyMongoStorage):
    assert pymongo_storage.resolve_state(value) == result
