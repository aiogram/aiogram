import pytest

from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.memory import MemoryStorage
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def state(bot: MockedBot):
    storage = MemoryStorage()
    ctx = storage.storage[bot][-42][42]
    ctx.state = "test"
    ctx.data = {"foo": "bar"}
    return FSMContext(bot=bot, storage=storage, user_id=-42, chat_id=42)


class TestFSMContext:
    async def test_address_mapping(self, bot: MockedBot):
        storage = MemoryStorage()
        ctx = storage.storage[bot][-42][42]
        ctx.state = "test"
        ctx.data = {"foo": "bar"}
        state = FSMContext(bot=bot, storage=storage, chat_id=-42, user_id=42)
        state2 = FSMContext(bot=bot, storage=storage, chat_id=42, user_id=42)
        state3 = FSMContext(bot=bot, storage=storage, chat_id=69, user_id=69)

        assert await state.get_state() == "test"
        assert await state2.get_state() is None
        assert await state3.get_state() is None

        assert await state.get_data() == {"foo": "bar"}
        assert await state2.get_data() == {}
        assert await state3.get_data() == {}

        await state2.set_state("experiments")
        assert await state.get_state() == "test"
        assert await state3.get_state() is None

        await state3.set_data({"key": "value"})
        assert await state2.get_data() == {}

        await state.update_data({"key": "value"})
        assert await state.get_data() == {"foo": "bar", "key": "value"}

        await state.clear()
        assert await state.get_state() is None
        assert await state.get_data() == {}

        assert await state2.get_state() == "experiments"
