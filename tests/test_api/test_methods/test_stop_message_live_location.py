from typing import Union

import pytest

from aiogram.methods import Request, StopMessageLiveLocation
from aiogram.types import Message
from tests.mocked_bot import MockedBot


class TestStopMessageLiveLocation:
    @pytest.mark.asyncio
    async def test_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(StopMessageLiveLocation, ok=True, result=True)

        response: Union[Message, bool] = await StopMessageLiveLocation(
            inline_message_id="inline message id"
        )
        request: Request = bot.get_request()
        assert request.method == "stopMessageLiveLocation"
        assert response == prepare_result.result

    @pytest.mark.asyncio
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(StopMessageLiveLocation, ok=True, result=True)

        response: Union[Message, bool] = await bot.stop_message_live_location(
            inline_message_id="inline message id"
        )
        request: Request = bot.get_request()
        assert request.method == "stopMessageLiveLocation"
        assert response == prepare_result.result
