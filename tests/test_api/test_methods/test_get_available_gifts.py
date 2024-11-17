from aiogram.methods import GetAvailableGifts
from aiogram.types import Gift, Gifts, Sticker
from tests.mocked_bot import MockedBot


class TestGetAvailableGifts:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetAvailableGifts,
            ok=True,
            result=Gifts(
                gifts=[
                    Gift(
                        id="gift_id",
                        sticker=Sticker(
                            file_id="file_id",
                            file_unique_id="file_id",
                            type="regular",
                            width=512,
                            height=512,
                            is_animated=False,
                            is_video=False,
                        ),
                        star_count=1,
                    )
                ]
            ),
        )

        response: Gifts = await bot.get_available_gifts()
        request = bot.get_request()
        assert response == prepare_result.result
