from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aiogram.exceptions import DataNotDictLikeError
from aiogram.fsm.state import State
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.pymongo import PyMongoStorage

STORAGE_KEY = StorageKey(bot_id=1, chat_id=1, user_id=1)


def _make_storage() -> PyMongoStorage:
    client_mock = MagicMock()
    storage = PyMongoStorage(client=client_mock)
    storage._collection = AsyncMock()
    return storage


class TestPyMongoStorageMock:
    def test_init_defaults(self):
        client_mock = MagicMock()
        storage = PyMongoStorage(client=client_mock)
        assert storage._client is client_mock
        assert storage._key_builder is not None

    def test_from_url(self):
        with patch("aiogram.fsm.storage.pymongo.AsyncMongoClient") as mock_client:
            storage = PyMongoStorage.from_url("mongodb://localhost:27017")
            assert isinstance(storage, PyMongoStorage)
            mock_client.assert_called_once()

    async def test_close(self):
        client_mock = AsyncMock()
        storage = PyMongoStorage(client=client_mock)
        await storage.close()
        client_mock.close.assert_called_once()

    def test_resolve_state_none(self):
        storage = _make_storage()
        assert storage.resolve_state(None) is None

    def test_resolve_state_state_object(self):
        storage = _make_storage()
        state = State(state="my_state")
        assert storage.resolve_state(state) == state.state

    def test_resolve_state_string(self):
        storage = _make_storage()
        assert storage.resolve_state("some_state") == "some_state"

    async def test_set_state_none_doc_has_other_data(self):
        storage = _make_storage()
        storage._collection.find_one_and_update.return_value = {"data": "x"}
        await storage.set_state(key=STORAGE_KEY, state=None)
        storage._collection.find_one_and_update.assert_called_once()
        storage._collection.delete_one.assert_not_called()

    async def test_set_state_none_empty_result_deletes_doc(self):
        storage = _make_storage()
        storage._collection.find_one_and_update.return_value = {}
        await storage.set_state(key=STORAGE_KEY, state=None)
        storage._collection.delete_one.assert_called_once()

    async def test_set_state_value(self):
        storage = _make_storage()
        await storage.set_state(key=STORAGE_KEY, state="active")
        storage._collection.update_one.assert_called_once()

    async def test_get_state_no_document(self):
        storage = _make_storage()
        storage._collection.find_one.return_value = None
        result = await storage.get_state(key=STORAGE_KEY)
        assert result is None

    async def test_get_state_with_value(self):
        storage = _make_storage()
        storage._collection.find_one.return_value = {"state": "active"}
        result = await storage.get_state(key=STORAGE_KEY)
        assert result == "active"

    async def test_set_data_invalid_type(self):
        storage = _make_storage()
        with pytest.raises(DataNotDictLikeError):
            await storage.set_data(key=STORAGE_KEY, data=())  # type: ignore[arg-type]

    async def test_set_data_empty_doc_has_other_data(self):
        storage = _make_storage()
        storage._collection.find_one_and_update.return_value = {"state": "x"}
        await storage.set_data(key=STORAGE_KEY, data={})
        storage._collection.find_one_and_update.assert_called_once()
        storage._collection.delete_one.assert_not_called()

    async def test_set_data_empty_deletes_doc(self):
        storage = _make_storage()
        storage._collection.find_one_and_update.return_value = {}
        await storage.set_data(key=STORAGE_KEY, data={})
        storage._collection.delete_one.assert_called_once()

    async def test_set_data_non_empty(self):
        storage = _make_storage()
        await storage.set_data(key=STORAGE_KEY, data={"foo": "bar"})
        storage._collection.update_one.assert_called_once()

    async def test_get_data_no_document(self):
        storage = _make_storage()
        storage._collection.find_one.return_value = None
        result = await storage.get_data(key=STORAGE_KEY)
        assert result == {}

    async def test_get_data_with_data(self):
        storage = _make_storage()
        storage._collection.find_one.return_value = {"data": {"foo": "bar"}}
        result = await storage.get_data(key=STORAGE_KEY)
        assert result == {"foo": "bar"}

    async def test_update_data_returns_data(self):
        storage = _make_storage()
        storage._collection.find_one_and_update.return_value = {"data": {"foo": "bar"}}
        result = await storage.update_data(key=STORAGE_KEY, data={"foo": "bar"})
        assert result == {"foo": "bar"}

    async def test_update_data_none_result_deletes_doc(self):
        storage = _make_storage()
        storage._collection.find_one_and_update.return_value = None
        result = await storage.update_data(key=STORAGE_KEY, data={"foo": "bar"})
        assert result == {}
        storage._collection.delete_one.assert_called_once()
