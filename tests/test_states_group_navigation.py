import pytest

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State


class FakeDispatcher:
    context = FSMContext(MemoryStorage(), chat=1, user=1)
    
    @classmethod
    def get_current(cls, no_error=True):
        return cls

    @classmethod
    def current_state(cls):
        return cls.context

    @classmethod
    def reset(cls):
        cls.context = FSMContext(MemoryStorage(), chat=1, user=1)


@pytest.fixture
async def reset_dispatcher():
    FakeDispatcher.reset()
    context = FakeDispatcher.get_current().current_state()
    current_state = await context.get_state()
    assert  current_state == None
    yield FakeDispatcher


class MyGroup(StatesGroup, dispatcher=FakeDispatcher()):
    state_1 = State()
    state_2 = State()


class TestNavigation:
    @pytest.mark.asyncio
    async def test_first(self, reset_dispatcher):
        state = await MyGroup.first()
        assert state == 'MyGroup:state_1'
    
    @pytest.mark.asyncio
    async def test_last(self, reset_dispatcher):
        state = await MyGroup.last()
        assert state == 'MyGroup:state_2'

    class TestNext:
        @pytest.mark.asyncio
        async def test_next_from_none(self, reset_dispatcher):
            state = await MyGroup.next()
            assert state == 'MyGroup:state_1'

        @pytest.mark.asyncio
        async def test_next_from_the_first_state(self, reset_dispatcher):
            await MyGroup.state_1.set()
            state = await MyGroup.next()
            assert state == 'MyGroup:state_2'

        @pytest.mark.asyncio
        async def test_next_from_the_last_state(self, reset_dispatcher):
            await MyGroup.last()
            state = await MyGroup.next()
            assert state == None

    class TestPrevious:
        @pytest.mark.asyncio
        async def test_previous_from_none(self, reset_dispatcher):
            state = await MyGroup.previous()
            assert state == 'MyGroup:state_1'

        @pytest.mark.asyncio
        async def test_previous_from_the_first_state(self, reset_dispatcher):
            await MyGroup.first()
            state = await MyGroup.previous()
            assert state == None

        @pytest.mark.asyncio
        async def test_previous_from_the_last_state(self, reset_dispatcher):
            await MyGroup.state_2.set()
            state = await MyGroup.previous()
            assert state == 'MyGroup:state_1'
