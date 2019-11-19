import datetime

import pytest

from aiogram.api.methods import Request, SendGame
from aiogram.api.types import Chat, Game, Message, PhotoSize
from tests.mocked_bot import MockedBot


class TestSendGame:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendGame,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                game=Game(
                    title="title",
                    description="description",
                    photo=[PhotoSize(file_id="file id", width=42, height=42)],
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await SendGame(chat_id=42, game_short_name="game")
        request: Request = bot.get_request()
        assert request.method == "sendGame"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            SendGame,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                game=Game(
                    title="title",
                    description="description",
                    photo=[PhotoSize(file_id="file id", width=42, height=42)],
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_game(chat_id=42, game_short_name="game")
        request: Request = bot.get_request()
        assert request.method == "sendGame"
        assert response == prepare_result.result
