import pytest

from aiogram.fsm.state import State
from aiogram.fsm.storage.mongo import MongoStorage, StorageKey
from tests.mocked_bot import MockedBot


@pytest.fixture(name="storage_key")
def create_storage_key(bot: MockedBot):
    return StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)


async def test_update_not_existing_data_with_empty_dictionary(
    mongo_storage: MongoStorage,
    storage_key: StorageKey,
):
    assert await mongo_storage._data_collection.find_one({}) is None
    assert await mongo_storage.get_data(key=storage_key) == {}
    assert await mongo_storage.update_data(key=storage_key, data={}) == {}
    assert await mongo_storage._data_collection.find_one({}) is None


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
