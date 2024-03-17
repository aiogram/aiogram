import pytest

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:
    raise ModuleNotFoundError(
        "You do not have the `motor` module installed to work with MongoDB. Install it with `pip install motor`"
    )

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.mongo import AIOGRAM_DATABASE_NAME


MONGO_TEST_URI: str = "mongodb+srv://bot:25sFG3vj7H2T4j5R@mongostorage-aiogram-te.pugxfxq.mongodb.net/?retryWrites=true&w=majority"
TEST_DATABASE_NAME: str = AIOGRAM_DATABASE_NAME


@pytest.fixture
async def mongo_storage():
    client = AsyncIOMotorClient(MONGO_TEST_URI)
    yield MongoStorage(client, database_name=TEST_DATABASE_NAME)
    client.close()


class TestMongoStorage:
    @pytest.mark.asyncio
    async def test_set_and_get_state(self, mongo_storage):
        chat_id = 123
        user_id = 456
        bot_id = 789
        key = StorageKey(chat_id=chat_id, user_id=user_id, bot_id=bot_id)

        # Set state
        await mongo_storage.set_state(key, State("some_state"))

        # Get state
        result = await mongo_storage.get_state(key)

        assert result == State("some_state")

    @pytest.mark.asyncio
    async def test_set_and_get_data(self, mongo_storage):
        chat_id = 123
        user_id = 456
        bot_id = 789
        key = StorageKey(chat_id=chat_id, user_id=user_id, bot_id=bot_id)

        # Set data
        await mongo_storage.set_data(key, {"key1": "value1", "key2": "value2"})

        # Get data
        result = await mongo_storage.get_data(key)

        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_update_data(self, mongo_storage):
        chat_id = 123
        user_id = 456
        bot_id = 789
        key = StorageKey(chat_id=chat_id, user_id=user_id, bot_id=bot_id)

        # Set initial data
        await mongo_storage.set_data(key, {"key1": "value1"})

        # Update data
        await mongo_storage.update_data(key, {"key2": "value2"})

        # Get updated data
        result = await mongo_storage.get_data(key)

        assert result == {"key1": "value1", "key2": "value2"}
