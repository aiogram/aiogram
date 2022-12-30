import datetime
from typing import Union

from aiogram.methods import EditMessageCaption, Request
from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


class TestEditMessageCaption:
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            EditMessageCaption,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="text",
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Union[Message, bool] = await EditMessageCaption()
        request: Request = bot.get_request()
        assert request.method == "editMessageCaption"
        assert response == prepare_result.result

    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            EditMessageCaption,
            ok=True,
            result=Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="text",
                chat=Chat(id=42, type="private"),
            ),
        )

        response: Union[Message, bool] = await bot.edit_message_caption()
        request: Request = bot.get_request()
        assert request.method == "editMessageCaption"
        assert response == prepare_result.result
