from aiogram.methods import GetChatShareThemeBackdrops
from aiogram.types import ChatShareThemeBackdrop, ChatShareThemeBackdrops, UniqueGiftBackdropColors
from tests.mocked_bot import MockedBot


class TestGetChatShareThemeBackdrops:
    async def test_bot_method(self, bot: MockedBot):
        prepare_result = bot.add_result_for(
            GetChatShareThemeBackdrops,
            ok=True,
            result=ChatShareThemeBackdrops(
                backdrops=[
                    ChatShareThemeBackdrop(
                        id=1,
                        name="backdrop",
                        colors=UniqueGiftBackdropColors(
                            center_color=1,
                            edge_color=2,
                            symbol_color=3,
                            text_color=4,
                        ),
                    )
                ]
            ),
        )

        response: ChatShareThemeBackdrops = await bot.get_chat_share_theme_backdrops()
        bot.get_request()
        assert response == prepare_result.result
