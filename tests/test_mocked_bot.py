from pathlib import Path

import pytest

from aiogram.exceptions import TelegramBadRequest, TelegramMigrateToChat, TelegramRetryAfter
from aiogram.methods import GetMe, SendMessage
from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


def test_mocked_bot_does_not_import_pydantic():
    source = (Path(__file__).parent / "mocked_bot.py").read_text(encoding="utf-8")
    assert "pydantic" not in source


async def test_success_result(bot: MockedBot):
    message = Message(message_id=1, date=0, chat=Chat(id=42, type="private"), text="hi")
    prepare_result = bot.add_result_for(SendMessage, ok=True, result=message)

    assert await bot.send_message(chat_id=42, text="hi") == prepare_result.result == message


@pytest.mark.parametrize(
    ("kwargs", "exception"),
    [
        ({"error_code": 400, "description": "Bad Request: oops"}, TelegramBadRequest),
        (
            {"error_code": 429, "description": "Too Many Requests", "retry_after": 5},
            TelegramRetryAfter,
        ),
        (
            {"error_code": 400, "description": "Migrated", "migrate_to_chat_id": -100},
            TelegramMigrateToChat,
        ),
    ],
)
async def test_error_mapping(bot: MockedBot, kwargs, exception):
    bot.add_result_for(GetMe, ok=False, **kwargs)

    with pytest.raises(exception):
        await bot.get_me()


async def test_requests_recorded_in_order(bot: MockedBot):
    for chat_id in (1, 2):
        bot.add_result_for(
            SendMessage,
            ok=True,
            result=Message(message_id=chat_id, date=0, chat=Chat(id=chat_id, type="private")),
        )

    await bot.send_message(chat_id=1, text="first")
    await bot.send_message(chat_id=2, text="second")

    assert [request.text for request in bot.session.requests] == ["first", "second"]
    assert bot.get_request().text == "second"
    assert not bot.session.closed
