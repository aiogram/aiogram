from typing import Union

from aiogram.methods import EditMessageLiveLocation, Request
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestEditMessageLiveLocation:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageLiveLocation, ok=True, result=True)

        response: Union[Message, bool] = await bot.edit_message_live_location(
            latitude=3.141592, longitude=3.141592
        )
        request = bot.get_request()
        assert response == prepare_result.result
