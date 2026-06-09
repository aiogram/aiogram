import asyncio
from datetime import datetime

from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot


class TestStateVSIsolation:
    async def test_issue(self, bot: MockedBot):
        dispatcher = Dispatcher(events_isolation=SimpleEventIsolation())
        first = 0
        second = 0
        third = 0
        stack = []

        class TestState(StatesGroup):
            foo = State()
            bar = State()
            baz = State()

        @dispatcher.message(Command("test"))
        async def command_top(message: Message, state: FSMContext):
            nonlocal first
            first += 1
            stack.append("command")
            await state.set_state(TestState.foo)

        @dispatcher.message(TestState.foo)
        async def handle_foo(message: Message, state: FSMContext):
            nonlocal second
            second += 1
            stack.append("foo")
            await state.set_state(TestState.bar)

        @dispatcher.message(TestState.bar)
        async def handle_bar(message: Message, state: FSMContext):
            nonlocal third
            third += 1
            stack.append("bar")
            await state.set_state(None)

        @dispatcher.message()
        async def handle_all(message: Message):
            stack.append("all")

        await asyncio.gather(
            *(
                dispatcher.feed_update(bot, update)
                for update in [
                    create_message_update(index=1, text="/test"),
                    create_message_update(index=2, text="foo"),
                    create_message_update(index=3, text="bar"),
                    create_message_update(index=4, text="baz"),
                ]
            )
        )

        # Before bug fix:
        #   first == 1, second == 3, third == 0, stack == ["command", "foo", "foo", "foo"]
        assert first == 1
        assert second == 1
        assert third == 1
        assert stack == ["command", "foo", "bar", "all"]


def create_message_update(index: int, text: str):
    return Update(
        update_id=index,
        message=Message(
            message_id=index,
            date=datetime.now(),
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test", username="test"),
            text=text,
        ),
    )
