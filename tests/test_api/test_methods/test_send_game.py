import datetime

from aiogram.methods import SendGame
from aiogram.types import Chat, Game, Message, PhotoSize
from tests.mocked_bot import MockedBot


class TestSendGame:
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
                    photo=[
                        PhotoSize(file_id="file id", width=42, height=42, file_unique_id="file id")
                    ],
                ),
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Message = await bot.send_game(chat_id=42, game_short_name="game")
        bot.get_request()
        assert response == prepare_result.result
