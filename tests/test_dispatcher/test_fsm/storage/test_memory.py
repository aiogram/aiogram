import pytest

from aiogram.dispatcher.fsm.storage.memory import MemoryStorage, MemoryStorageRecord


@pytest.fixture()
def storage():
    return MemoryStorage()


class TestMemoryStorage:
    @pytest.mark.asyncio
    async def test_set_state(self, storage: MemoryStorage):
        assert await storage.get_state(chat_id=-42, user_id=42) is None

        await storage.set_state(chat_id=-42, user_id=42, state="state")
        assert await storage.get_state(chat_id=-42, user_id=42) == "state"

        assert -42 in storage.storage
        assert 42 in storage.storage[-42]
        assert isinstance(storage.storage[-42][42], MemoryStorageRecord)
        assert storage.storage[-42][42].state == "state"

    @pytest.mark.asyncio
    async def test_set_data(self, storage: MemoryStorage):
        assert await storage.get_data(chat_id=-42, user_id=42) == {}

        await storage.set_data(chat_id=-42, user_id=42, data={"foo": "bar"})
        assert await storage.get_data(chat_id=-42, user_id=42) == {"foo": "bar"}

        assert -42 in storage.storage
        assert 42 in storage.storage[-42]
        assert isinstance(storage.storage[-42][42], MemoryStorageRecord)
        assert storage.storage[-42][42].data == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_update_data(self, storage: MemoryStorage):
        assert await storage.get_data(chat_id=-42, user_id=42) == {}
        assert await storage.update_data(chat_id=-42, user_id=42, data={"foo": "bar"}) == {
            "foo": "bar"
        }
        assert await storage.update_data(chat_id=-42, user_id=42, data={"baz": "spam"}) == {
            "foo": "bar",
            "baz": "spam",
        }
