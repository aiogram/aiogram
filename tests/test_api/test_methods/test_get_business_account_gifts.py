import datetime

from aiogram.methods import GetBusinessAccountGifts
from aiogram.types import Gift, OwnedGiftRegular, OwnedGifts, Sticker
from tests.mocked_bot import MockedBot


class TestGetBusinessAccountGifts:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetBusinessAccountGifts,
            ok=True,
            result=OwnedGifts(
                total_count=1,
                gifts=[
                    OwnedGiftRegular(
                        gift=Gift(
                            id="test_gift_id",
                            sticker=Sticker(
                                file_id="test_file_id",
                                file_unique_id="test_file_unique_id",
                                type="regular",
                                width=512,
                                height=512,
                                is_animated=False,
                                is_video=False,
                            ),
                            star_count=100,
                        ),
                        send_date=int(datetime.datetime.now().timestamp()),
                    )
                ],
            ),
        )

        response: OwnedGifts = await bot.get_business_account_gifts(
            business_connection_id="test_connection_id",
            limit=10,
        )
        request = bot.get_request()
        assert response == prepare_result.result
