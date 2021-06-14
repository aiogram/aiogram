import pytest

from aiogram.dispatcher.fsm.storage.base import BaseStorage
from tests.mocked_bot import MockedBot


@pytest.mark.parametrize(
    "storage",
    [pytest.lazy_fixture("redis_storage"), pytest.lazy_fixture("memory_storage")],
)
class TestStorages:
    @pytest.mark.asyncio
    async def test_lock(self, bot: MockedBot, storage: BaseStorage):
        # TODO: ?!?
        async with storage.lock(bot=bot, chat_id=-42, user_id=42):
            assert True, "You are kidding me?"

    @pytest.mark.asyncio
    async def test_set_state(self, bot: MockedBot, storage: BaseStorage):
        assert await storage.get_state(bot=bot, chat_id=-42, user_id=42) is None

        await storage.set_state(bot=bot, chat_id=-42, user_id=42, state="state")
        assert await storage.get_state(bot=bot, chat_id=-42, user_id=42) == "state"
        await storage.set_state(bot=bot, chat_id=-42, user_id=42, state=None)
        assert await storage.get_state(bot=bot, chat_id=-42, user_id=42) is None

    @pytest.mark.asyncio
    async def test_set_data(self, bot: MockedBot, storage: BaseStorage):
        assert await storage.get_data(bot=bot, chat_id=-42, user_id=42) == {}

        await storage.set_data(bot=bot, chat_id=-42, user_id=42, data={"foo": "bar"})
        assert await storage.get_data(bot=bot, chat_id=-42, user_id=42) == {"foo": "bar"}
        await storage.set_data(bot=bot, chat_id=-42, user_id=42, data={})
        assert await storage.get_data(bot=bot, chat_id=-42, user_id=42) == {}

    @pytest.mark.asyncio
    async def test_update_data(self, bot: MockedBot, storage: BaseStorage):
        assert await storage.get_data(bot=bot, chat_id=-42, user_id=42) == {}
        assert await storage.update_data(
            bot=bot, chat_id=-42, user_id=42, data={"foo": "bar"}
        ) == {"foo": "bar"}
        assert await storage.update_data(
            bot=bot, chat_id=-42, user_id=42, data={"baz": "spam"}
        ) == {"foo": "bar", "baz": "spam"}
        assert await storage.get_data(bot=bot, chat_id=-42, user_id=42) == {
            "foo": "bar",
            "baz": "spam",
        }
