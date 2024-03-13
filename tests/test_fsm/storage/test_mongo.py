import pytest

from aiogram.fsm.state import State
from aiogram.fsm.storage.mongo import MongoStorage, StorageKey
from tests.mocked_bot import MockedBot

PREFIX = "fsm"
CHAT_ID = -42
USER_ID = 42


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=CHAT_ID, user_id=USER_ID, bot_id=bot.id)


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
