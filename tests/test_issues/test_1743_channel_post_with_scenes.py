from datetime import datetime

import pytest

from aiogram import Dispatcher, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, SceneRegistry, on
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import Chat, Message, Update
from tests.mocked_bot import MockedBot

CHANNEL_ID = -1001234567890


class BrowseScene(Scene, state="browse"):
    pass


class ChannelStateScene(Scene, state="channel_state"):
    @on.channel_post()
    async def save_message_id(
        self,
        message: Message,
        state: FSMContext,
    ) -> int:
        await state.update_data(last_message_id=message.message_id)
        return message.message_id


@pytest.mark.parametrize("update_type", ["channel_post", "edited_channel_post"])
async def test_channel_events_with_scenes_do_not_require_fsm_state(
    bot: MockedBot,
    update_type: str,
):
    dispatcher = Dispatcher()
    channel_router = Router()

    if update_type == "channel_post":
        channel_router.channel_post.filter(F.chat.id == CHANNEL_ID)

        @channel_router.channel_post()
        async def on_channel_post(message: Message):
            return message.message_id
    else:
        channel_router.edited_channel_post.filter(F.chat.id == CHANNEL_ID)

        @channel_router.edited_channel_post()
        async def on_edited_channel_post(message: Message):
            return message.message_id

    dispatcher.include_router(channel_router)
    SceneRegistry(dispatcher).add(BrowseScene)

    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=CHANNEL_ID, type="channel"),
        text="test",
    )

    kwargs = {"update_id": 1, update_type: message}
    update = Update(**kwargs)

    result = await dispatcher.feed_update(bot, update)
    assert result == 1


async def test_channel_scene_has_fsm_state_with_chat_strategy(bot: MockedBot):
    dispatcher = Dispatcher(fsm_strategy=FSMStrategy.CHAT)
    router = Router()

    @router.channel_post((F.chat.id == CHANNEL_ID) & (F.text == "enter"))
    async def enter_channel_state(message: Message, state: FSMContext):
        await state.set_state(ChannelStateScene.__scene_config__.state)
        return message.message_id

    dispatcher.include_router(router)
    SceneRegistry(dispatcher).add(ChannelStateScene)

    initial_update = Update(
        update_id=1,
        channel_post=Message(
            message_id=10,
            date=datetime.now(),
            chat=Chat(id=CHANNEL_ID, type="channel"),
            text="enter",
        ),
    )
    await dispatcher.feed_update(bot, initial_update)

    active_state = await dispatcher.fsm.storage.get_state(
        key=dispatcher.fsm.get_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=CHANNEL_ID,
        ).key
    )
    assert active_state == ChannelStateScene.__scene_config__.state

    scene_update = Update(
        update_id=2,
        channel_post=Message(
            message_id=11,
            date=datetime.now(),
            chat=Chat(id=CHANNEL_ID, type="channel"),
            text="scene",
        ),
    )
    result = await dispatcher.feed_update(bot, scene_update)
    assert result == 11
    state_data = await dispatcher.fsm.storage.get_data(
        key=dispatcher.fsm.get_context(
            bot=bot,
            chat_id=CHANNEL_ID,
            user_id=CHANNEL_ID,
        ).key
    )
    assert state_data["last_message_id"] == 11
