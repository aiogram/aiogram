from datetime import datetime

import pytest

from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot

OWN_USER_ID = 200
GUEST_CALLER_ID = 100


def private_message(message_id: int, from_id: int, **kwargs) -> Message:
    # A guest summon in the private chat of users 100 and 200 is reported
    # with the id of user 200, which is also the id of the bot's own chat with them
    return Message(
        message_id=message_id,
        date=datetime.now(),
        chat=Chat(id=OWN_USER_ID, type="private"),
        from_user=User(id=from_id, is_bot=False, first_name="Test"),
        text="test",
        **kwargs,
    )


@pytest.mark.parametrize("strategy", list(FSMStrategy))
async def test_guest_message_does_not_share_state_with_own_chat(
    bot: MockedBot,
    strategy: FSMStrategy,
):
    dispatcher = Dispatcher(
        storage=MemoryStorage(),
        events_isolation=SimpleEventIsolation(),
        fsm_strategy=strategy,
    )
    seen = {}

    @dispatcher.message()
    async def start_order(message: Message, state: FSMContext):
        await state.set_state("order:address")
        await state.update_data(address="draft")

    @dispatcher.guest_message()
    async def guest_reply(message: Message, state: FSMContext):
        seen["state"] = await state.get_state()
        seen["data"] = await state.get_data()
        seen["key"] = state.key
        await state.clear()

    await dispatcher.feed_update(
        bot, Update(update_id=1, message=private_message(1, from_id=OWN_USER_ID))
    )
    await dispatcher.feed_update(
        bot,
        Update(
            update_id=2,
            guest_message=private_message(2, from_id=GUEST_CALLER_ID, guest_query_id="gq-1"),
        ),
    )

    assert seen["key"].is_guest is True
    assert seen["state"] is None
    assert seen["data"] == {}

    own_state = dispatcher.fsm.get_context(bot=bot, chat_id=OWN_USER_ID, user_id=OWN_USER_ID)
    assert await own_state.get_state() == "order:address"
    assert await own_state.get_data() == {"address": "draft"}
    await dispatcher.fsm.close()
