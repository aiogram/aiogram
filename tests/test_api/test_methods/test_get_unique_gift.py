from aiogram.methods import GetUniqueGift
from aiogram.types import (
    Sticker,
    UniqueGift,
    UniqueGiftBackdrop,
    UniqueGiftBackdropColors,
    UniqueGiftModel,
    UniqueGiftSymbol,
)
from tests.mocked_bot import MockedBot

STICKER = Sticker(
    file_id="file_id",
    file_unique_id="file_unique_id",
    type="regular",
    width=512,
    height=512,
    is_animated=False,
    is_video=False,
)


class TestGetUniqueGift:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetUniqueGift,
            ok=True,
            result=UniqueGift(
                gift_id="gift_id",
                base_name="gift",
                name="gift-1",
                number=1,
                model=UniqueGiftModel(name="model", sticker=STICKER, rarity_per_mille=100),
                symbol=UniqueGiftSymbol(name="symbol", sticker=STICKER, rarity_per_mille=100),
                backdrop=UniqueGiftBackdrop(
                    name="backdrop",
                    colors=UniqueGiftBackdropColors(
                        center_color=1,
                        edge_color=2,
                        symbol_color=3,
                        text_color=4,
                    ),
                    rarity_per_mille=100,
                ),
            ),
        )

        response: UniqueGift = await bot.get_unique_gift(name="gift-1")
        request = bot.get_request()
        assert request.name == "gift-1"
        assert response == prepare_result.result
