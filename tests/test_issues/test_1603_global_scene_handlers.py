from datetime import datetime, timezone

import pytest
from examples.scene_global_handlers import EchoScene, create_dispatcher

from aiogram import Dispatcher
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot


def make_update(text: str, update_id: int = 1) -> Update:
    return Update(
        update_id=update_id,
        message=Message(
            message_id=update_id,
            date=datetime.now(timezone.utc),
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test"),
            text=text,
        ),
    )


async def feed_message(dispatcher: Dispatcher, bot: MockedBot, text: str) -> SendMessage:
    update = make_update(text)
    bot.add_result_for(SendMessage, ok=True, result=update.message)
    await dispatcher.feed_update(bot, update)
    request = bot.get_request()
    assert isinstance(request, SendMessage)
    return request


@pytest.mark.parametrize("inside_scene", [False, True])
@pytest.mark.parametrize(
    ("command", "response"),
    [
        ("/help", "Use /start to enter the scene and /cancel to leave it."),
        ("/cancel", "Cancelled."),
    ],
)
async def test_global_commands_inside_and_outside_scenes(
    bot: MockedBot, inside_scene: bool, command: str, response: str
) -> None:
    dispatcher = create_dispatcher()
    state = dispatcher.fsm.get_context(bot=bot, chat_id=42, user_id=42)
    if inside_scene:
        await feed_message(dispatcher, bot, "/start")
        assert await state.get_state() == EchoScene.__scene_config__.state

    request = await feed_message(dispatcher, bot, command)

    assert request.text == response
    expected_state = (
        EchoScene.__scene_config__.state if inside_scene and command == "/help" else None
    )
    assert await state.get_state() == expected_state
    assert not bot.session.requests


async def test_scene_continues_after_help_and_stops_after_cancel(bot: MockedBot) -> None:
    dispatcher = create_dispatcher()
    await feed_message(dispatcher, bot, "/start")

    request = await feed_message(dispatcher, bot, "before help")
    assert request.text == "Scene received: before help"

    await feed_message(dispatcher, bot, "/help")
    request = await feed_message(dispatcher, bot, "after help")
    assert request.text == "Scene received: after help"

    await feed_message(dispatcher, bot, "/cancel")
    result = await dispatcher.feed_update(bot, make_update("after cancel"))
    assert result is UNHANDLED
    assert not bot.session.requests
