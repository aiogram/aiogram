from typing import Union

import pytest

from aiogram.api.methods import EditMessageLiveLocation, Request
from aiogram.api.types import Message
from tests.mocked_bot import MockedBot


class TestEditMessageLiveLocation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageLiveLocation, ok=True, result=True)

        response: Union[Message, bool] = await EditMessageLiveLocation(
            latitude=3.141592, longitude=3.141592
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageLiveLocation"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(EditMessageLiveLocation, ok=True, result=True)

        response: Union[Message, bool] = await bot.edit_message_live_location(
            latitude=3.141592, longitude=3.141592
        )
        request: Request = bot.get_request()
        assert request.method == "editMessageLiveLocation"
        assert response == prepare_result.result
