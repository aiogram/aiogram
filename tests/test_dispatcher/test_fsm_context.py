import pytest
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext


class TestFSMContext:
    @pytest.mark.asyncio
    async def test_update_data(self):
        context = FSMContext(MemoryStorage(), chat=1, user=1)
        async with context.proxy() as data:
            data.update(key1="value1", key2="value2")
        async with context.proxy() as data:
            assert data['key1'] == "value1"
            assert data['key2'] == "value2"
