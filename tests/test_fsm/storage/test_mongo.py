import pytest
from pymongo.errors import PyMongoError

from aiogram.fsm.state import State
from aiogram.fsm.storage.mongo import MongoStorage, StorageKey
from tests.conftest import CHAT_ID, USER_ID

PREFIX = "fsm"


async def test_get_storage_passing_only_url(mongo_server):
    storage = MongoStorage.from_url(url=mongo_server)
    try:
        await storage._client.server_info()
    except PyMongoError as e:
        pytest.fail(str(e))


async def test_update_not_existing_data_with_empty_dictionary(
    mongo_storage: MongoStorage,
    storage_key: StorageKey,
):
    assert await mongo_storage._collection.find_one({}) is None
    assert await mongo_storage.get_data(key=storage_key) == {}
    assert await mongo_storage.update_data(key=storage_key, data={}) == {}
    assert await mongo_storage._collection.find_one({}) is None


async def test_document_life_cycle(
    mongo_storage: MongoStorage,
    storage_key: StorageKey,
):
    assert await mongo_storage._collection.find_one({}) is None
    await mongo_storage.set_state(storage_key, "test")
    await mongo_storage.set_data(storage_key, {"key": "value"})
    assert await mongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "state": "test",
        "data": {"key": "value"},
    }
    await mongo_storage.set_state(storage_key, None)
    assert await mongo_storage._collection.find_one({}) == {
        "_id": f"{PREFIX}:{CHAT_ID}:{USER_ID}",
        "data": {"key": "value"},
    }
    await mongo_storage.set_data(storage_key, {})
    assert await mongo_storage._collection.find_one({}) is None


class TestStateAndDataDoNotAffectEachOther:
    async def test_state_and_data_do_not_affect_each_other_while_getting(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        assert await mongo_storage._collection.find_one({}) is None
        await mongo_storage.set_state(storage_key, "test")
        await mongo_storage.set_data(storage_key, {"key": "value"})
        assert await mongo_storage.get_state(storage_key) == "test"
        assert await mongo_storage.get_data(storage_key) == {"key": "value"}

    async def test_data_do_not_affect_to_deleted_state_getting(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")
        await mongo_storage.set_data(storage_key, {"key": "value"})
        await mongo_storage.set_state(storage_key, None)
        assert await mongo_storage.get_state(storage_key) is None

    async def test_state_do_not_affect_to_deleted_data_getting(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")
        await mongo_storage.set_data(storage_key, {"key": "value"})
        await mongo_storage.set_data(storage_key, {})
        assert await mongo_storage.get_data(storage_key) == {}

    async def test_state_do_not_affect_to_updating_not_existing_data_with_empty_dictionary(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test"
        }
        assert await mongo_storage.update_data(key=storage_key, data={}) == {}
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test"
        }

    async def test_state_do_not_affect_to_updating_not_existing_data_with_non_empty_dictionary(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test"
        }
        assert await mongo_storage.update_data(
            key=storage_key,
            data={"key": "value"},
        ) == {"key": "value"}
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }

    async def test_state_do_not_affect_to_updating_existing_data_with_empty_dictionary(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")
        await mongo_storage.set_data(storage_key, {"key": "value"})
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }
        assert await mongo_storage.update_data(key=storage_key, data={}) == {"key": "value"}
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }

    async def test_state_do_not_affect_to_updating_existing_data_with_non_empty_dictionary(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")
        await mongo_storage.set_data(storage_key, {"key": "value"})
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "value"},
        }
        assert await mongo_storage.update_data(
            key=storage_key,
            data={"key": "VALUE", "key_2": "value_2"},
        ) == {"key": "VALUE", "key_2": "value_2"}
        assert await mongo_storage._collection.find_one({}, projection={"_id": 0}) == {
            "state": "test",
            "data": {"key": "VALUE", "key_2": "value_2"},
        }


class TestGetValue:
    async def test_get_existing_value(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_data(
            storage_key, {"key": "value", "number": 42, "list": [1, 2, 3]}
        )

        assert await mongo_storage.get_value(storage_key, "key") == "value"
        assert await mongo_storage.get_value(storage_key, "number") == 42
        assert await mongo_storage.get_value(storage_key, "list") == [1, 2, 3]

    async def test_get_non_existing_value(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_data(storage_key, {"key": "value"})

        assert await mongo_storage.get_value(storage_key, "non_existing_key") is None
        assert (
            await mongo_storage.get_value(storage_key, "non_existing_key", default="default")
            == "default"
        )

    async def test_get_value_from_non_existing_document(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        assert await mongo_storage._collection.find_one({}) is None

        assert await mongo_storage.get_value(storage_key, "any_key") is None
        assert (
            await mongo_storage.get_value(storage_key, "any_key", default="default") == "default"
        )

    async def test_get_value_with_document_containing_only_state(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
    ):
        await mongo_storage.set_state(storage_key, "test")

        document = await mongo_storage._collection.find_one({})
        assert document is not None
        assert "data" not in document

        assert await mongo_storage.get_value(storage_key, "any_key") is None
        assert (
            await mongo_storage.get_value(storage_key, "any_key", default="default") == "default"
        )

    async def test_get_value_uses_projection(
        self,
        mongo_storage: MongoStorage,
        storage_key: StorageKey,
        monkeypatch,
    ):
        await mongo_storage.set_data(
            storage_key, {"key1": "value1", "key2": "value2", "key3": {"nested": "data"}}
        )

        original_find_one = mongo_storage._collection.find_one
        calls = []

        async def mock_find_one(*args, **kwargs):
            calls.append(kwargs)
            return await original_find_one(*args, **kwargs)

        monkeypatch.setattr(mongo_storage._collection, "find_one", mock_find_one)

        value = await mongo_storage.get_value(storage_key, "key2")

        assert len(calls) == 1
        assert "projection" in calls[0]
        assert calls[0]["projection"] == {"_id": 0, "data.key2": 1}
        assert value == "value2"


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
def test_resolve_state(value, result, mongo_storage: MongoStorage):
    assert mongo_storage.resolve_state(value) == result
